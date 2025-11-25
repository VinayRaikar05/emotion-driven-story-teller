import os
import subprocess
import json
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from parser_gender import *
from emotion_detection import predict_emotion, emotion_classifier

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],  # Frontend development servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/generate-audio")
async def generate_audio():
    try:
        # Define paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ngrok_script = os.path.join(current_dir, 'ngrok.py')
        story_path = os.path.join(current_dir, "story.json")

        # Ensure story.json exists
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

        # Get the generated audio file
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