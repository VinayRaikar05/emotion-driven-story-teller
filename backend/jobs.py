"""
Job queue management using RQ (Redis Queue).
Handles enqueueing TTS generation jobs and processing them asynchronously.
"""

import os
import uuid
import json
import logging
from typing import Dict
from rq import Queue, get_current_job
from redis import Redis

logger = logging.getLogger(__name__)

# Redis connection (configured via environment)
redis_conn = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=False  # We'll handle binary data for audio
)

# Job queue
job_queue = Queue('tts', connection=redis_conn)


def enqueue_tts_job(story_data: list) -> str:
    """
    Enqueue a TTS generation job.
    
    Args:
        story_data: List of dialogues with emotions and genders
        
    Returns:
        job_id: Unique identifier for tracking this job
    """
    job_id = str(uuid.uuid4())
    
    logger.info(f"Enqueueing TTS job: {job_id}")
    
    job = job_queue.enqueue(
        process_tts_job,
        story_data,
        job_id,
        job_id=job_id,
        job_timeout='30m',  # 30 minute timeout
        result_ttl=86400  # Keep result for 24 hours
    )
    
    return job_id


def process_tts_job(story_data: list, job_id: str):
    """
    Worker function that processes TTS generation.
    Called asynchronously by RQ worker.
    
    Args:
        story_data: List of dialogue entries with emotions and genders
        job_id: Unique job identifier
    """
    try:
        from backend.tts_client import generate_story_audio
    except ImportError:
        # Fallback for when running worker from backend directory
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from tts_client import generate_story_audio
    try:
        from backend.s3_helper import S3Helper
    except ImportError:
        from s3_helper import S3Helper
    
    logger.info(f"Processing TTS job: {job_id}")
    
    # Update job status
    current_job = get_current_job()
    current_job.meta['status'] = 'processing'
    current_job.meta['progress'] = 0
    current_job.save_meta()
    
    try:
        # Generate audio using TTS client
        logger.info(f"Generating audio for job: {job_id}")
        audio_path = generate_story_audio(story_data, job_id)
        
        current_job.meta['progress'] = 70
        current_job.save_meta()
        
        # Upload to S3
        logger.info(f"Uploading audio to S3 for job: {job_id}")
        s3_helper = S3Helper()
        s3_key = s3_helper.upload_to_s3(audio_path, job_id)
        
        current_job.meta['progress'] = 90
        current_job.save_meta()
        
        # Generate presigned URL (7 day expiry)
        download_url = s3_helper.generate_presigned_url(s3_key, expiry=604800)
        
        # Update job with success
        current_job.meta['status'] = 'completed'
        current_job.meta['progress'] = 100
        current_job.meta['download_url'] = download_url
        current_job.meta['s3_key'] = s3_key
        current_job.save_meta()
        
        logger.info(f"Job {job_id} completed successfully")
        
        # Clean up local file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        current_job.meta['status'] = 'failed'
        current_job.meta['error'] = str(e)
        current_job.save_meta()
        raise


def get_job_status(job_id: str) -> Dict:
    """
    Get current status of a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Dictionary with status, progress, download_url, and error (if any)
    """
    job = job_queue.fetch_job(job_id)
    
    if not job:
        return {
            'status': 'not_found',
            'error': 'Job ID not found'
        }
    
    # Check job state
    if job.is_queued:
        status = 'queued'
    elif job.is_started:
        status = job.meta.get('status', 'processing')
    elif job.is_finished:
        status = job.meta.get('status', 'completed')
    elif job.is_failed:
        status = 'failed'
    else:
        status = 'unknown'
    
    return {
        'job_id': job_id,
        'status': status,
        'progress': job.meta.get('progress', 0),
        'download_url': job.meta.get('download_url'),
        'error': job.meta.get('error'),
        's3_key': job.meta.get('s3_key')
    }


def check_redis_connection() -> bool:
    """
    Check if Redis is accessible.
    Used for health checks.
    
    Returns:
        True if Redis is accessible, False otherwise
    """
    try:
        redis_conn.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False
