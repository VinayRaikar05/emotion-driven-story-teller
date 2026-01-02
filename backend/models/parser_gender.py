import os
import re
import json
import unicodedata
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
from tensorflow.keras.regularizers import l2
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.utils import resample
from llama_index.core import SimpleDirectoryReader


### 🔹 Function to Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF and fixes Unicode issues."""
    reader = SimpleDirectoryReader(input_files=[pdf_path])
    documents = reader.load_data()

    # Normalize Unicode and replace curly apostrophes
    text = "\n".join([unicodedata.normalize("NFKD", doc.text) for doc in documents])
    text = text.replace("\u2019", "'")  # Fix curly apostrophe issue

    return text


### 🔹 Function to Parse Dialogue & Narration Correctly
def parse_dialogues_and_narration(text):
    """Extracts dialogues and narration correctly, ensuring proper grouping."""
    dialogues = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Strategy:
        # 1. Attempt to parse as Dialogue Line "Name: Content"
        # 2. If valid dialogue, handle Name (strip attrs) and Content (extract narration)
        # 3. If NOT dialogue, extract any narration (...) and treat rest as Narration from "Narrator" if significant.

        # Regex for Dialogue Line: Name (up to 50 chars) + Colon + Content
        # We use a broad regex and refine later
        # Allowing (...) in name part
        dialogue_match = re.match(r"^([\w\s\.\(\)\"“”'-]{1,50}):\s*(.*)", line)
        
        is_dialogue = False
        if dialogue_match:
            raw_name = dialogue_match.group(1).strip()
            raw_content = dialogue_match.group(2).strip()
            
            # Check: Name shouldn't be PURELY parens like "(One Day)" -> That's narration
            if not (raw_name.startswith("(") and raw_name.endswith(")")):
                is_dialogue = True
                
                # 1. Clean Name
                # Remove parentheticals (attributes)
                clean_name = re.sub(r"\s*\(.*?\)", "", raw_name).strip()
                
                # Filter out likely metadata or non-characters
                IGNORED_NAMES = {"Title", "Author", "By", "Page", "Scene", "Act", "Chapter", "Date", "Time", "Setting"}
                if clean_name in IGNORED_NAMES or len(clean_name) > 30 or not clean_name:
                    is_dialogue = False # False alarm, probably metadata
                else:
                     # 2. Process Content for Narration
                     # Extract "(...)" from content as separate narration entries
                     # But we need to preserve order.
                     # "Hello (smiles) friend" -> "Hello", "Narrator: smiles", "friend"
                     # Complex to split. strict "dialogue" list entry doesn't support sub-narration well
                     # unless we split into multiple entries?
                     # For now, let's just strip narration from dialogue for Audio purity, 
                     # OR keep it if it's acting instruction?
                     # The current system treats "Narrator" as a separate block.
                     
                     # Simple approach: Extract narration to buffer BEFORE/AFTER? 
                     # Usually (action) is visual. 
                     # Let's extract all (...) from content and add as Narrator lines?
                     # Risk: "friend" part might be lost or split.
                     # Let's keep it simple: Strip (...) from dialogue for TTS (cleaned), 
                     # but maybe we don't need to extract it as separate Narrator line if it's just action?
                     # User complaint: "cant detect story... audio not playable... emotions incorrect"
                     # Reading "(smiles)" is annoying.
                     
                     narration_in_dialogue = re.findall(r"\((.*?)\)", raw_content)
                     # Optional: Add these as narrator lines? 
                     # If I add them, I need to know where (before/after).
                     # Let's just add them AFTER for now (simplified), or IGNORE (clean audio).
                     # User wants "correct detection".
                     # Reading "(smiles)" is annoying.
                     
                     clean_dialogue = re.sub(r"\s*\(.*?\)", "", raw_content).strip()
                     
                     # Remove quotes
                     if (clean_dialogue.startswith('"') and clean_dialogue.endswith('"')) or \
                        (clean_dialogue.startswith('“') and clean_dialogue.endswith('”')):
                         clean_dialogue = clean_dialogue[1:-1].strip()

                     if clean_dialogue:
                        dialogues.append({
                            "name": clean_name,
                            "dialogue": clean_dialogue
                        })
                        
                     # If we found narration in dialogue, maybe append it after?
                     # for narr in narration_in_dialogue:
                     #    dialogues.append({"name": "Narrator", "dialogue": narr, "predicted_gender": "Male"})
                     # Let's Skip this for now to keep it clean.

        if not is_dialogue:
            # Not a dialogue line (or was metadata)
            # Treat as Narration / Description
            
            # Extract all (...)
            while "(" in line and ")" in line:
                before, narration, after = re.split(r"\((.*?)\)", line, 1)
                if narration.strip():
                     dialogues.append({
                        "name": "Narrator", 
                        "dialogue": narration.strip(),
                        "predicted_gender": "Male"
                    })
                line = str(before) + " " + str(after)
                line = line.strip()
            
            # If text remains (unquoted, unparenthesized description)
            # ex: "The rain had been falling..."
            if line:
                 dialogues.append({
                    "name": "Narrator",
                    "dialogue": line,
                    "predicted_gender": "Male"
                })

    return dialogues


### 🔹 Function to Convert Name to ASCII Sequence
def name_to_ascii(name, max_length=15):
    """Converts a name into an ASCII sequence for input into the LSTM model."""
    name_ascii = [ord(char) for char in name.lower()][:max_length]
    name_ascii += [0] * (max_length - len(name_ascii))  # Pad with zeros
    return np.array(name_ascii).reshape(1, -1)


### 🔹 Function to Predict Gender from Name
def predict_gender(name, model):
    """Predicts gender ('Male' or 'Female') based on a given name using LSTM model."""
    name_ascii = name_to_ascii(name)
    prediction = model.predict(name_ascii)[0][0]
    return "Female" if prediction > 0.5 else "Male"


### 🔹 Function to Load Trained Model
def load_trained_model(model_path):
    """Loads the pre-trained LSTM model for gender classification."""
    if os.path.exists(model_path):
        model = load_model(model_path)
        print("✅ Model successfully loaded.")
        return model
    else:
        raise FileNotFoundError("❌ Model file not found!")


### 🔹 Function to Add Predicted Gender to Dialogues
def add_gender_to_dialogues(dialogues, model):
    """Adds gender prediction to each dialogue entry based on character name."""
    for entry in dialogues:
        if entry["name"] != "Narrator":  # Skip narrator
            entry["predicted_gender"] = predict_gender(entry["name"], model)
    return dialogues


### 🔹 Main Function
def main():
    # Paths
    model_path = "lstm_gender_model.h5"
    pdf_path = "Story.pdf"

    # Load trained model
    model = load_trained_model(model_path)

    # Extract and parse dialogues from PDF
    text = extract_text_from_pdf(pdf_path)
    dialogues = parse_dialogues_and_narration(text)

    # Add gender predictions
    updated_dialogues = add_gender_to_dialogues(dialogues, model)

    # Output JSON without escaping characters
    json_output = json.dumps(updated_dialogues, indent=4, ensure_ascii=False)
    print(json_output)


if __name__ == "__main__":
    main()