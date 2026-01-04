"""
ElevenLabs TTS client with retry logic, concurrency limiting, and circuit breaker.
Production-ready implementation with proper error handling.
"""

import os
import time
import requests
from typing import Optional, Dict, List, Union
from threading import Semaphore
from functools import wraps
import logging
import subprocess
import shutil
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Concurrency limiter (max 2 parallel requests to respect API limits)
CONCURRENCY_LIMIT = Semaphore(2)


class CircuitBreaker:
    """
    Simple circuit breaker implementation to prevent cascading failures.
    Opens after threshold failures, closes after timeout period.
    """
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False
    
    def call(self, func):
        """Execute function with circuit breaker protection"""
        if self.is_open:
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("Circuit breaker closing - timeout expired")
                self.is_open = False
                self.failure_count = 0
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")
        
        try:
            result = func()
            # Success - reset failure count
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")
            
            raise


# Global circuit breaker instance
circuit_breaker = CircuitBreaker()


def retry_with_backoff(max_retries=3, base_delay=1):
    """
    Decorator for exponential backoff retry logic.
    Handles HTTP 429 rate limits with Retry-After header support.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except requests.HTTPError as e:
                    if e.response.status_code == 429:
                        # Rate limited - check Retry-After header
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            delay = int(retry_after)
                            logger.warning(f"Rate limited. Retry-After: {delay}s")
                        else:
                            delay = base_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Rate limited. Exponential backoff: {delay}s")
                        
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                            continue
                        else:
                            logger.error("Max retries exceeded for rate limiting")
                            raise
                    
                    elif attempt == max_retries - 1:
                        logger.error(f"HTTP error after {max_retries} attempts: {e}")
                        raise
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}). Retrying after {delay}s...")
                    time.sleep(delay)
                    
        return wrapper
    return decorator


class TTSClient:
    """ElevenLabs TTS client with production-ready features"""
    
    # Voice mappings from Colab notebook
    VOICE_MAPPING = {
        "male_1": "pqHfZKP75CvOlQylNhV4",    # Bill
        "male_2": "iP95p4xoKVk53GoZ742B",    # Chris
        "male_3": "bVMeCyTHy58xNoL34h3p",    # Jeremy
        "female_1": "Xb7hH8MSUJpSbSDYk0k2",  # Alice
        "female_2": "MF3mGyEYCl7XYWbV9V6O",  # Ellie
        "female_3": "XB0fDUnXU5powFXDhCwa",  # Charlotte
        "narrator": "nPczCjzI2devNBz1zQrb"   # Brian
    }
    
    # Emotion settings from Colab notebook
    EMOTION_SETTINGS = {
        "neutral": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.5},
        "happy": {"stability": 0.3, "similarity_boost": 0.9, "style": 0.9},
        "sad": {"stability": 0.6, "similarity_boost": 0.5, "style": 0.7},
        "angry": {"stability": 0.2, "similarity_boost": 1.0, "style": 0.8},
        "fearful": {"stability": 0.4, "similarity_boost": 0.9, "style": 0.9},
        "surprised": {"stability": 0.3, "similarity_boost": 1.0, "style": 1.0},
        "disgusted": {"stability": 0.7, "similarity_boost": 0.5, "style": 0.6},
    }
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("ElevenLabs API key is required")
        self.api_key = api_key.strip()
        self.base_url = "https://api.elevenlabs.io/v1"
        self.character_voice_mapping = {}
        self.available_male_voices = ["male_1", "male_2", "male_3"]
        self.available_female_voices = ["female_1", "female_2", "female_3"]
        
    def get_unique_character_voice(self, character: str, gender: str) -> str:
        """
        Assign unique voice to each character.
        Logic extracted from Colab notebook.
        """
        if character == "narrator":
            return self.VOICE_MAPPING["narrator"]
        
        if character in self.character_voice_mapping:
            return self.character_voice_mapping[character]
        
        if gender.lower() == "male":
            if not self.available_male_voices:
                self.available_male_voices = ["male_1", "male_2", "male_3"]
            selected_voice = self.available_male_voices.pop(
                random.randint(0, len(self.available_male_voices) - 1)
            )
        else:
            if not self.available_female_voices:
                self.available_female_voices = ["female_1", "female_2", "female_3"]
            selected_voice = self.available_female_voices.pop(
                random.randint(0, len(self.available_female_voices) - 1)
            )
        
        self.character_voice_mapping[character] = self.VOICE_MAPPING[selected_voice]
        return self.character_voice_mapping[character]
    
    @retry_with_backoff(max_retries=3)
    def generate_speech(
        self,
        text: str,
        voice_id: str,
        voice_settings: Optional[Dict] = None
    ) -> bytes:
        """
        Generate speech audio from text using ElevenLabs API.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            voice_settings: Voice configuration (stability, similarity_boost, style)
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        with CONCURRENCY_LIMIT:  # Limit concurrent requests
            def make_request():
                url = f"{self.base_url}/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_turbo_v2"
                }
                if voice_settings:
                    payload["voice_settings"] = voice_settings
                
                print(f"DEBUG: Generating speech for text (length: {len(text)})")
                print(f"DEBUG: Using Model ID: {payload.get('model_id')}")
                print(f"DEBUG: Key Prefix: {self.api_key[:5] if self.api_key else 'None'}")
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                
                return response.content
            
            return circuit_breaker.call(make_request)

def generate_with_edge_tts(text: str, voice: str, output_path: str):
    """Fallback generation using EdgeTTS CLI (prevents async loop conflicts)"""
    try:
        # Use simple CLI command
        # Ensure text doesn't break CLI (basic sanitization)
        sanitized_text = text.replace('"', '\\"')
        cmd = ["edge-tts", "--text", text, "--write-media", output_path, "--voice", voice]
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"EdgeTTS failed: {e.stderr}")
        raise


def generate_story_audio(story_data: List[Dict], job_id: str) -> Union[str, List[str]]:
    """
    Generate complete story audio from dialogue data.
    Orchestrates multiple TTS calls and merges them.
    
    Args:
        story_data: List of dialogue entries with name, dialogue, gender, emotion
        job_id: Job identifier for file naming
        
    Returns:
        Path to generated MP3 file OR List of paths (if merge failed/skipped)
    """
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        # Fallback to provided key
        api_key = "sk_e84c43552fbdeb61d35e4c86050632eec7801f74e572c46b"
    
    if api_key:
        api_key = api_key.strip()
    
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable not set")
    
    client = TTSClient(api_key)
    output_dir = f"/tmp/audio_{job_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    audio_files = []
    
    logger.info(f"Generating audio for {len(story_data)} dialogue entries")
    
    for i, dialogue in enumerate(story_data):
        try:
            # Get voice for character
            voice_id = client.get_unique_character_voice(
                dialogue["name"],
                dialogue.get("predicted_gender", "male")
            )
            
            # Get emotion settings
            emotion = dialogue.get("emotion", "neutral")
            voice_settings = client.EMOTION_SETTINGS.get(emotion, client.EMOTION_SETTINGS["neutral"])
            
            # Generate speech
            audio_data = client.generate_speech(
                dialogue["dialogue"],
                voice_id,
                voice_settings
            )
            
            # Save to file
            file_path = os.path.join(output_dir, f"{i:04d}_{dialogue['name']}_{emotion}.mp3")
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            audio_files.append(file_path)
            
            # Rate limiting - wait 2 seconds between requests
            if i < len(story_data) - 1:
                time.sleep(2)
                
        except Exception as e:
            logger.warning(f"ElevenLabs generation failed for dialogue {i}: {e}. specific_error='{type(e).__name__}'")
            logger.info("Attempting fallback to EdgeTTS (Free)...")
            
            try:
                # Determine fallback voice
                raw_gender = dialogue.get("predicted_gender")
                gender = raw_gender.lower() if raw_gender else "male"
                name = dialogue["name"]
                
                if name == "Narrator":
                    edge_voice = "en-US-ChristopherNeural"
                elif gender == "female":
                    edge_voice = "en-US-AriaNeural"
                else:
                    edge_voice = "en-US-GuyNeural"
                
                # Define path (same as intended)
                file_path = os.path.join(output_dir, f"{i:04d}_{dialogue['name']}_{emotion}.mp3")
                
                # Generate
                generate_with_edge_tts(dialogue["dialogue"], edge_voice, file_path)
                
                audio_files.append(file_path)
                logger.info(f"Fallback successful for dialogue {i}")
                
            except Exception as fallback_error:
                logger.error(f"Both ElevenLabs and EdgeTTS failed for dialogue {i}: {fallback_error}")
                # We can choose to skip this line or raise. Raising ensures transparency.
                raise e # Raise original error if fallback also fails
    
    # Merge all audio files
    logger.info(f"Merging {len(audio_files)} audio files")
    merged_path = merge_audio_files(audio_files, job_id)
    
    # Cleanup individual files
    for file_path in audio_files:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return merged_path




def merge_audio_files(audio_files: List[str], job_id: str) -> Union[str, List[str]]:
    """
    Merge multiple audio files.
    Tries to use ffmpeg for high quality merge with pauses.
    Returns list of input files if ffmpeg is missing (Playlist Mode).
    """
    output_path = f"/tmp/final_story_{job_id}.mp3"

    # Fallback to playlist mode if ffmpeg is not installed
    # Browser cannot play concatenated mp3s reliably, so we return the list
    if not shutil.which("ffmpeg"):
        logger.warning("ffmpeg not found in PATH. Returning unmerged file list for playlist playback.")
        return audio_files

    # FFmpeg implementation
    # Generate silence files first (easier than complex filter generation for variable lengths)
    silence_files = []
    temp_dir = f"/tmp/audio_{job_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    concat_list_path = os.path.join(temp_dir, "concat_list.txt")
    
    try:
        with open(concat_list_path, "w") as f:
            for i, file_path in enumerate(audio_files):
                if not os.path.exists(file_path):
                    logger.warning(f"Skipping missing file: {file_path}")
                    continue
                    
                # Add the audio file
                # Escape path for ffmpeg concat file
                safe_path = file_path.replace("\\", "/")
                f.write(f"file '{safe_path}'\n")
                
                # Determine pause duration
                pause_duration_ms = 500
                if i == len(audio_files) - 1:
                    pause_duration_ms += 500
                    
                # Create silence file
                silence_path = os.path.join(temp_dir, f"silence_{i}.mp3")
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", 
                    f"anullsrc=r=24000:cl=mono", "-t", f"{pause_duration_ms/1000}", 
                    "-q:a", "2", silence_path
                ], check=True, capture_output=True)
                
                safe_silence_path = silence_path.replace('\\', '/')
                f.write(f"file '{safe_silence_path}'\n")
                silence_files.append(silence_path)

        # Run ffmpeg concat
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                "-i", concat_list_path, "-c", "copy", output_path
            ], check=True, capture_output=True)
            
            logger.info(f"Merged audio saved to {output_path}")
            
            # Cleanup silence files
            for sf in silence_files:
                if os.path.exists(sf):
                    os.remove(sf)
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
                
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg merge failed: {e.stderr}. Fallback to playlist mode.")
            # Fallback to playlist mode
            return audio_files

    except Exception as e:
        logger.error(f"Error during audio merge: {str(e)}. Fallback to playlist mode.")
        return audio_files
