import torch
from transformers import pipeline

# Load pre-trained emotion classification model
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)

# Custom corrections for emotion classification with expanded emotional indicators
custom_corrections = {
    "neutral": ["Excuse me", "Mind if I join", "Miss", "Sir", "Please", "Pardon me", "Well", "Hmm", "Maybe", "I see", "Indeed", "Alright", "Okay", "Sure"],
    "joy": ["Beautiful", "Wonderful", "Peaceful", "Happy", "Exciting", "Great news", "Thank you", "Thanks", "Love", "Delighted", "Fantastic", "Amazing", "Awesome", "Brilliant", "Perfect", "Excellent", "Yay", "Hooray", "Cheers", "Blessed", "Lucky", "Grateful", "Pleased"],
    "sadness": ["Weep", "Alone", "I'm sorry", "Apologize", "Regret", "Lost", "Mourn", "Depressed", "Heartbroken", "Miss you", "Grief", "Disappointed", "Hurt", "Painful", "Suffering", "Crying", "Tears", "Lonely", "Hopeless", "Miserable"],
    "surprise": ["Really?", "You think so?", "No way!", "Unbelievable", "Wow", "Oh my god", "What?", "Seriously?", "Amazing!", "Incredible!", "Unexpected", "Shocking", "Astonishing", "Stunned", "Startled", "Surprised", "Speechless"],
    "disgust": ["Sigh", "Ugh", "Disgusting", "Gross", "That's nasty", "Revolting", "Horrible", "Awful", "Yuck", "Eww", "Sick", "Repulsive", "Distasteful", "Offensive", "Unpleasant", "Nauseating"],
    "anger": ["Outrageous", "How dare you", "This is unfair", "I'm furious", "Angry", "Mad", "Rage", "Hate", "Frustrated", "Annoyed", "Irritated", "Furious", "Livid", "Enraged", "Hostile", "Bitter", "Resent", "Damn", "Upset"],
    "fear": ["Terrified", "Scared", "Horrified", "Dread", "I'm afraid", "Frightened", "Panic", "Worried", "Anxious", "Nervous", "Trembling", "Shaking", "Petrified", "Paranoid", "Threatened", "Help!", "Dangerous", "Scared to death"]
}

# Function to predict emotion
def predict_emotion(dialogue_entry):
    name = dialogue_entry.name
    text = dialogue_entry.dialogue.lower()
    
    # Narrator's emotion should always be neutral
    if name == "Narrator":
        return "neutral"
    
    # Initialize emotion scores
    emotion_scores = {emotion: 0 for emotion in custom_corrections.keys()}
    
    # Check for custom corrections with weighted scoring
    for emotion, keywords in custom_corrections.items():
        for keyword in keywords:
            if keyword.lower() in text:
                # Add higher weight for exact matches or stronger emotional indicators
                if keyword.lower() == text.strip():
                    emotion_scores[emotion] += 2
                else:
                    emotion_scores[emotion] += 1
    
    # If we have strong custom matches, use the highest scoring emotion
    max_score = max(emotion_scores.values())
    if max_score >= 1:
        max_emotions = [e for e, s in emotion_scores.items() if s == max_score]
        if len(max_emotions) == 1:
            return max_emotions[0]
    
    # If no strong custom matches, use the model prediction
    result = emotion_classifier(text)
    predicted_emotion = result[0][0]['label']
    
    # Ensure predicted emotion is in our predefined list
    allowed_emotions = {"anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"}
    if predicted_emotion in allowed_emotions:
        # If we had weak custom matches, combine them with the model prediction
        if emotion_scores[predicted_emotion] > 0:
            return predicted_emotion
        # If the model is confident but no custom matches, use the model's prediction
        elif result[0][0]['score'] > 0.6:
            return predicted_emotion
    
    # If no strong signals, check for any emotion with at least some score
    max_custom_score = max(emotion_scores.values())
    if max_custom_score > 0:
        return max(emotion_scores.items(), key=lambda x: x[1])[0]
    
    return "neutral"