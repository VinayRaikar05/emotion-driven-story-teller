import os
import subprocess
import json
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from models.parser_gender import *
from models.emotion_detection import predict_emotion, emotion_classifier

# Import new async job processing system
try:
    try:
        from backend.jobs import enqueue_tts_job, get_job_status, check_redis_connection
    except ImportError:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from jobs import enqueue_tts_job, get_job_status, check_redis_connection
        
    ASYNC_JOBS_AVAILABLE = True
except ImportError as e:
    ASYNC_JOBS_AVAILABLE = False
    print(f"Warning: Async job processing not available. Error: {e}")

# Import monitoring tools
try:
    from prometheus_client import Counter, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
    
    # Prometheus metrics
    request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Import Sentry for error tracking
try:
    import sentry_sdk
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv('ENVIRONMENT', 'development'),
            traces_sample_rate=0.1
        )
        print("Sentry error tracking initialized")
except ImportError:
    pass

# Configure structured logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(message)s'  # JSON format will be added by middleware
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
# Get CORS origins from environment or use defaults
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://localhost:5174')
allowed_origins = [origin.strip() for origin in cors_origins.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests in structured JSON format"""
    start_time = datetime.now()
    
    response = await call_next(request)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Structured log entry
    log_data = {
        "timestamp": start_time.isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_seconds": round(duration, 4)
    }
    
    logger.info(json.dumps(log_data))
    
    # Update Prometheus metrics if available
    if PROMETHEUS_AVAILABLE:
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        request_duration.observe(duration)
    
    return response

# Initialize model path
MODEL_PATH = os.path.join(os.path.dirname(__file__), "lstm_gender_model.h5")

# Load model on startup
try:
    model = load_trained_model(MODEL_PATH)
except FileNotFoundError:
    model = None

class StoryScript(BaseModel):
    text: str

class DialogueEntry(BaseModel):
    name: str
    dialogue: str
    predicted_gender: Optional[str] = None
    emotion: Optional[str] = None

class DialogueList(BaseModel):
    dialogues: List[DialogueEntry]

@app.post("/upload-script", response_model=List[DialogueEntry])
async def upload_script(file: UploadFile = File(...)):
    """Process a script file and return dialogues with gender predictions."""
    if not model:
        raise HTTPException(
            status_code=503,
            detail="Gender detection model not loaded. Please ensure model file exists."
        )
    
    # Validate file format
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Create a temporary file path
        temp_file_path = os.path.join(os.path.dirname(__file__), "temp_upload.pdf")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Extract text from PDF
            text = extract_text_from_pdf(temp_file_path)
            
            # Parse dialogues from script
            dialogues = parse_dialogues_and_narration(text)
            
            # Add gender predictions only
            updated_dialogues = add_gender_to_dialogues(dialogues, model)
            
            return updated_dialogues
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect-emotions", response_model=List[DialogueEntry])
async def detect_emotions(dialogues: DialogueList):
    """Process dialogues and add emotion predictions."""
    try:
        # Add emotion predictions
        updated_dialogues = []
        for entry in dialogues.dialogues:
            try:
                entry_dict = entry.dict()
                entry_dict['emotion'] = predict_emotion(entry)
                updated_dialogues.append(entry_dict)
            except Exception as e:
                print(f"Error processing entry {entry.name}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error processing entry {entry.name}: {str(e)}")
        
        # Save the processed dialogues to story.json
        story_path = os.path.join(os.path.dirname(__file__), "story.json")
        try:
            with open(story_path, 'w', encoding='utf-8') as f:
                json.dump(updated_dialogues, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to story.json: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving to story.json: {str(e)}")
        
        return updated_dialogues
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=str(e))
        raise e


@app.post("/generate-audio", status_code=202)
async def generate_audio():
    """
    Enqueue TTS generation job (async).
    Returns immediately with job_id for polling.
    """
    if not ASYNC_JOBS_AVAILABLE:
        # Fallback to legacy sync mode if async not available
        logger.warning("Using legacy synchronous TTS generation")
        return await generate_audio_legacy()
    
    try:
        # Get story data
        story_path = os.path.join(os.path.dirname(__file__), "story.json")
        
        if not os.path.exists(story_path):
            raise HTTPException(
                status_code=400,
                detail="No story data found. Please process the story with /detect-emotions first."
            )
        
        with open(story_path, 'r') as f:
            story_data = json.load(f)
        
        # Enqueue job for async processing
        job_id = enqueue_tts_job(story_data)
        
        logger.info(f"TTS job enqueued with ID: {job_id}")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "status_url": f"/jobs/{job_id}",
            "message": "TTS generation job queued. Poll status_url for progress."
        }
        
    except Exception as e:
        logger.error(f"Error enqueueing TTS job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """
    Poll job status and get download URL when complete.
    
    Returns:
        - status: queued, processing, completed, failed, not_found
        - progress: 0-100 (if available)
        - download_url: S3 presigned URL (when completed)
        - error: Error message (if failed)
    """
    if not ASYNC_JOBS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Async job processing not available. Please use legacy endpoint."
        )
    
    try:
        status = get_job_status(job_id)
        return status
    except Exception as e:
        logger.error(f"Error fetching job status for {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "api": "up",
            "gender_model": "loaded" if model else "not_loaded",
            "emotion_model": "loaded",  # Always loaded from HuggingFace
            "async_jobs": "available" if ASYNC_JOBS_AVAILABLE else "unavailable"
        }
    }
    
    # Check Redis connection if async jobs available
    if ASYNC_JOBS_AVAILABLE:
        health_status["services"]["redis"] = "connected" if check_redis_connection() else "disconnected"
    
    return health_status


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Prometheus metrics not available. Install prometheus-client."
        )
    
    return Response(generate_latest(), media_type="text/plain")


# Legacy synchronous endpoint (fallback)
async def generate_audio_legacy():
    """
    Legacy synchronous TTS generation using ngrok.
    Only used if async job system is not available.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ngrok_script = os.path.join(current_dir, 'ngrok.py')
        story_path = os.path.join(current_dir, "story.json")

        if not os.path.exists(story_path):
            raise HTTPException(status_code=400, detail="No story data found. Please process the story first.")

        # Run ngrok script
        result = subprocess.run(
            [sys.executable, ngrok_script],
            check=True,
            cwd=current_dir,
            capture_output=True,
            text=True
        )

        audio_path = os.path.join(current_dir, "audio_output", "final_story.mp3")
        if not os.path.exists(audio_path):
            raise HTTPException(
                status_code=500,
                detail=f"Audio file not generated. Script output: {result.stdout}\nError: {result.stderr}"
            )

        return FileResponse(audio_path, media_type="audio/mpeg", filename="final_story.mp3")

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running ngrok script: {e.stdout}\nError: {e.stderr}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))