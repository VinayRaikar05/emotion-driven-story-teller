"""
Tests for PDF parsing and dialogue extraction.
"""

import pytest
from backend.models.parser_gender import parse_dialogues_and_narration

def test_parse_dialogues_basic():
    """Test basic dialogue parsing"""
    text = '''
    Alice: "Hello, how are you?"
    Bob: "I'm doing great, thanks!"
    (Alice smiles warmly)
    '''
    
    dialogues = parse_dialogues_and_narration(text)
    
    assert len(dialogues) >= 2
    assert any(d['name'] == 'Alice' for d in dialogues)
    assert any(d['name'] == 'Bob' for d in dialogues)
    
    # Check dialogue content
    alice_dialogue = next((d for d in dialogues if d['name'] == 'Alice'), None)
    assert alice_dialogue is not None
    assert "Hello" in alice_dialogue['dialogue']


def test_parse_narration():
    """Test narration extraction"""
    text = "(The sun sets over the horizon)"
    dialogues = parse_dialogues_and_narration(text)
    
    assert len(dialogues) == 1
    assert dialogues[0]['name'] == 'narrator'
    assert "sun sets" in dialogues[0]['dialogue']


def test_mixed_dialogue_and_narration():
    """Test parsing mixed dialogue and narration"""
    text = '''
    (The story begins)
    Alice: "Welcome everyone!"
    (The crowd cheers)
    Bob: "Thank you for coming!"
    '''
    
    dialogues = parse_dialogues_and_narration(text)
    
    # Should have 4 entries (2 narrations + 2 dialogues)
    assert len(dialogues) == 4
    
    # Count narrations and dialogues
    narrations = [d for d in dialogues if d['name'] == 'narrator']
    actual_dialogues = [d for d in dialogues if d['name'] != 'narrator']
    
    assert len(narrations) == 2
    assert len(actual_dialogues) == 2


def test_empty_text():
    """Test parsing empty text"""
    dialogues = parse_dialogues_and_narration("")
    assert isinstance(dialogues, list)
    assert len(dialogues) == 0
