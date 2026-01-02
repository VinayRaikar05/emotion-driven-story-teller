import torch
from transformers import pipeline

# Load pre-trained emotion classification model
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)

# Custom corrections for emotion classification - Keyword boosting
# These will increase confidence in a specific emotion but won't strictly override the AI model
# unless the match is very strong.
custom_corrections = {
    "joy": ["Beautiful", "Wonderful", "Happy", "Exciting", "Great news", "Thank you", "Thanks", "Love", "Delighted", "Fantastic", "Amazing", "Awesome", "Brilliant", "Perfect", "Excellent", "Yay", "Hooray", "Cheers", "Blessed", "Lucky", "Grateful", "Pleased"],
    "sadness": ["Weep", "Alone", "I'm sorry", "Apologize", "Regret", "Lost", "Mourn", "Depressed", "Heartbroken", "Miss you", "Grief", "Disappointed", "Hurt", "Painful", "Suffering", "Crying", "Tears", "Lonely", "Hopeless", "Miserable", "Alas"],
    "surprise": ["Really?", "No way!", "Unbelievable", "Wow", "Oh my god", "Seriously?", "Amazing!", "Incredible!", "Unexpected", "Shocking", "Astonishing", "Stunned", "Startled", "Surprised", "Speechless"],
    "disgust": ["Ugh", "Disgusting", "Gross", "Nasty", "Revolting", "Horrible", "Awful", "Yuck", "Eww", "Sick", "Repulsive", "Distasteful", "Offensive", "Nauseating"],
    "anger": ["Outrageous", "How dare you", "Unfair", "Furious", "Angry", "Mad", "Rage", "Hate", "Frustrated", "Annoyed", "Irritated", "Livid", "Enraged", "Hostile", "Bitter", "Resent", "Damn", "Upset"],
    "fear": ["Terrified", "Scared", "Horrified", "Dread", "Afraid", "Frightened", "Panic", "Worried", "Anxious", "Nervous", "Trembling", "Shaking", "Petrified", "Paranoid", "Threatened", "Help!", "Dangerous"]
}

# Function to predict emotion
def predict_emotion(dialogue_entry):
    name = dialogue_entry.name
    text = dialogue_entry.dialogue.lower()
    
    # Narrator's emotion should always be neutral (but can be tweaked if needed)
    if name == "Narrator":
        return "neutral"
    
    # Run the AI model first to get the baseline prediction
    result = emotion_classifier(text)
    
    # Handle potential nested list output (common with top_k=1)
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        prediction = result[0][0]
    elif isinstance(result, list) and len(result) > 0:
        prediction = result[0]
    else:
        # Fallback
        prediction = {'label': 'neutral', 'score': 0.0}

    model_emotion = prediction['label']
    model_score = prediction['score']
    
    # Initialize score map with model prediction
    emotion_scores = {emotion: 0 for emotion in custom_corrections.keys()}
    emotion_scores["neutral"] = 0
    
    # Give the model a base weight (0.8 to 1.0 depending on confidence)
    if model_emotion in emotion_scores:
        emotion_scores[model_emotion] += (1.0 + model_score)
    else:
        # If model returns an emotion we don't track, map it or ignore (usually 'neutral' is default)
        emotion_scores["neutral"] += 1.0

    # Keyword boosting
    for emotion, keywords in custom_corrections.items():
        for keyword in keywords:
            kw_lower = keyword.lower()
            if kw_lower in text:
                # Strong signal: The text IS the keyword (e.g. "Wow")
                if text.strip() == kw_lower:
                    emotion_scores[emotion] += 3.0
                # Medium signal: The keyword is at the start (e.g. "Wow, look at that")
                elif text.startswith(kw_lower):
                     emotion_scores[emotion] += 1.5
                # Weak signal: The keyword is inside
                else:
                    emotion_scores[emotion] += 0.5
    
    # Determine the winner
    best_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
    
    return best_emotion