"""
S3/MinIO storage helper with presigned URL generation.
Supports both AWS S3 and MinIO for local development.
"""

import boto3
from botocore.exceptions import ClientError
import os
import logging

logger = logging.getLogger(__name__)


class S3Helper:
    """Helper for S3/MinIO operations"""
    
    def __init__(self):
        """
        Initialize S3 client.
        Reads configuration from environment variables.
        Supports both AWS S3 and MinIO (for local dev).
        """
        endpoint_url = os.getenv('S3_ENDPOINT')  # Set for MinIO, empty for AWS S3
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'emotion-storyteller-audio')
        
        # Create bucket if it doesn't exist (for MinIO)
        if endpoint_url:
            self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist (for local MinIO)"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")
    
    def upload_to_s3(self, file_path: str, job_id: str) -> str:
        """
        Upload audio file to S3.
        
        Args:
            file_path: Local path to audio file
            job_id: Job identifier for organizing files
            
        Returns:
            S3 key of uploaded file
        """
        s3_key = f"audio/{job_id}/final_story.mp3"
        
        try:
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'audio/mpeg',
                    'ContentDisposition': 'attachment; filename="final_story.mp3"'
                }
            )
            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
    
    def generate_presigned_url(self, s3_key: str, expiry: int = 3600) -> str:
        """
        Generate presigned URL for downloading audio.
        
        Args:
            s3_key: S3 object key
            expiry: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned download URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiry
            )
            logger.info(f"Generated presigned URL for {s3_key}, expires in {expiry}s")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_object(self, s3_key: str):
        """
        Delete object from S3.
        
        Args:
            s3_key: S3 object key to delete
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted {s3_key} from S3")
        except ClientError as e:
            logger.error(f"Failed to delete from S3: {e}")
            raise


# S3 Lifecycle Rule Configuration (Documentation)
# ================================================
# 
# For production deployments, configure S3 bucket with lifecycle rule 
# to automatically delete old audio files after 7 days:
#
# AWS CLI Command:
# ----------------
# aws s3api put-bucket-lifecycle-configuration \
#     --bucket emotion-storyteller-audio \
#     --lifecycle-configuration file://lifecycle.json
# 
# lifecycle.json:
# ---------------
# {
#   "Rules": [{
#     "Id": "DeleteOldAudio",
#     "Prefix": "audio/",
#     "Status": "Enabled",
#     "Expiration": {
#       "Days": 7
#     }
#   }]
# }
#
# For MinIO (local development):
# -------------------------------
# MinIO also supports lifecycle rules via mc command:
# mc ilm add local/emotion-storyteller-audio \
#     --expiration-days 7 \
#     --prefix "audio/"
