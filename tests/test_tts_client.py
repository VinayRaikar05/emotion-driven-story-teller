"""
Tests for TTS client retry logic, backoff, and circuit breaker.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import requests
import time
from backend.tts_client import TTSClient, retry_with_backoff, CircuitBreaker


def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures"""
    cb = CircuitBreaker(failure_threshold=3, timeout=60)
    
    def failing_func():
        raise Exception("Simulated failure")
    
    # Should fail 3 times before opening
    for i in range(3):
        with pytest.raises(Exception, match="Simulated failure"):
            cb.call(failing_func)
        
        # Circuit should not be open yet on last failure
        if i < 2:
            assert not cb.is_open
    
    # After 3 failures, circuit should be open
    assert cb.is_open
    assert cb.failure_count == 3
    
    # Next call should fail immediately without calling function
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        cb.call(failing_func)


def test_circuit_breaker_closes_after_timeout():
    """Test circuit breaker closes after timeout period"""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.1)  # 100ms timeout
    
    def failing_func():
        raise Exception("Simulated failure")
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)
    
    assert cb.is_open
    
    # Wait for timeout
    time.sleep(0.15)
    
    # Should be able to try again (circuit closed)
    # This will fail and increment counter, but proves circuit closed
    with pytest.raises(Exception, match="Simulated failure"):
        cb.call(failing_func)
    
    # Should have reset and started counting again
    assert cb.failure_count == 1


def test_retry_with_backoff_success_on_retry():
    """Test retry succeeds after initial failure"""
    attempt_count = [0]
    
    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def sometimes_failing_func():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise requests.RequestException("Temporary failure")
        return "success"
    
    result = sometimes_failing_func()
    assert result == "success"
    assert attempt_count[0] == 2  # Failed once, succeeded on retry


def test_retry_with_backoff_respects_retry_after():
    """Test retry respects Retry-After header on 429"""
    
    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def rate_limited_func():
        response = Mock()
        response.status_code = 429
        response.headers = {'Retry-After': '1'}
        raise requests.HTTPError(response=response)
    
    start_time = time.time()
    
    with pytest.raises(requests.HTTPError):
        rate_limited_func()
    
    elapsed = time.time() - start_time
    # Should have waited for retries (at least 2 seconds total for 2 retries)
    assert elapsed >= 2.0


def test_retry_gives_up_after_max_retries():
    """Test retry gives up after max attempts"""
    attempt_count = [0]
    
    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def always_failing_func():
        attempt_count[0] += 1
        raise requests.RequestException("Always fails")
    
    with pytest.raises(requests.RequestException, match="Always fails"):
        always_failing_func()
    
    assert attempt_count[0] == 3  # Should have tried 3 times


@patch('requests.post')
def test_tts_client_successful_generation(mock_post):
    """Test successful TTS generation"""
    mock_response = Mock()
    mock_response.content = b"fake_audio_data"
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    client = TTSClient(api_key="test_key")
    
    audio = client.generate_speech(
        text="Hello world",
        voice_id="test_voice_id",
        voice_settings={"stability": 0.5}
    )
    
    assert audio == b"fake_audio_data"
    assert mock_post.called


def test_tts_client_requires_api_key():
    """Test that TTSClient requires API key"""
    with pytest.raises(ValueError, match="API key is required"):
        TTSClient(api_key="")
    
    with pytest.raises(ValueError, match="API key is required"):
        TTSClient(api_key=None)
