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
    narration_buffer = []

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Identify and extract narration
        while "(" in line and ")" in line:
            before, narration, after = re.split(r"\((.*?)\)", line, 1)

            # Add any narration found
            if narration.strip():
                narration_buffer.append(narration.strip())

            # Process remaining text after narration
            line = after.strip()

        # If narration was found and processed, add it to the list
        if narration_buffer:
            dialogues.append({
                "name": "Narrator",
                "dialogue": " ".join(narration_buffer),
                "predicted_gender": "Male"
            })
            narration_buffer = []

        # Process character dialogue (everything outside `()`)
        if line:
            match = re.match(r"^(\w+):\s*\"(.*?)\"", line)
            if match:
                char_name = match.group(1)
                char_dialogue = match.group(2)

                dialogues.append({
                    "name": char_name,
                    "dialogue": char_dialogue
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