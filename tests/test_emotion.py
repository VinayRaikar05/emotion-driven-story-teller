"""
Tests for emotion detection with mocked HuggingFace model.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.models.emotion_detection import predict_emotion


@patch('backend.models.emotion_detection.emotion_classifier')
def test_emotion_detection_happy(mock_classifier):
    """Test emotion detection for happy dialogue"""
    mock_classifier.return_value = [{'label': 'joy', 'score': 0.9}]
    
    entry = {
        "name": "Alice",
        "dialogue": "I'm so happy and excited today!",
        "predicted_gender": "Female"
    }
    
    emotion = predict_emotion(entry)
    assert emotion in ['happy', 'joy']


@patch('backend.models.emotion_detection.emotion_classifier')
def test_emotion_detection_sad(mock_classifier):
    """Test emotion detection for sad dialogue"""
    mock_classifier.return_value = [{'label': 'sadness', 'score': 0.85}]
    
    entry = {
        "name": "Bob",
        "dialogue": "I feel so sad about what happened.",
        "predicted_gender": "Male"
    }
    
    emotion = predict_emotion(entry)
    assert emotion in ['sad', 'sadness']


@patch('backend.models.emotion_detection.emotion_classifier')
def test_emotion_detection_neutral(mock_classifier):
    """Test fallback to ML model for neutral text"""
    mock_classifier.return_value = [{'label': 'neutral', 'score': 0.7}]
    
    entry = {
        "name": "Charlie",
        "dialogue": "The meeting is scheduled for 3pm tomorrow.",
        "predicted_gender": "Male"
    }
    
    emotion = predict_emotion(entry)
    assert emotion == 'neutral'


@patch('backend.models.emotion_detection.emotion_classifier')
def test_keyword_override(mock_classifier):
    """Test that strong keywords override ML model"""
    # Even if model says neutral, strong keywords should win
    mock_classifier.return_value = [{'label': 'neutral', 'score': 0.6}]
    
    entry = {
        "name": "Dave",
        "dialogue": "Hooray! We won the championship!",
        "predicted_gender": "Male"
    }
    
    # Should detect 'Hooray' keyword and return joy/happy
    emotion = predict_emotion(entry)
    # Keyword-based detection should override
    assert emotion in ['joy', 'happy']
