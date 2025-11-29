import requests
import json

TEST_KEY = "sk_e84c43552fbdeb61d35e4c86050632eec7801f74e572c46b"
FAILING_VOICE_ID = "MF3mGyEYCl7XYWbV9V6O" # Ellie

# Settings from tts_client.py for "neutral" (default) or others
VOICE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.8, "style": 0.5}

def debug_exact_request(key):
    print(f"🔍 Testing Exact Request for Voice: {FAILING_VOICE_ID}")
    headers = {"xi-api-key": key, "Content-Type": "application/json"}
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{FAILING_VOICE_ID}"
    payload = {
        "text": "Testing exact request parameters.",
        "model_id": "eleven_turbo_v2",
        "voice_settings": VOICE_SETTINGS
    }
    
    try:
        print(f"Sending request with model: {payload['model_id']} and settings: {payload['voice_settings']}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ Success! The exact request works.")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_exact_request(TEST_KEY)
