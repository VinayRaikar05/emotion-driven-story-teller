import os
from dotenv import load_dotenv

# Try to load .env as the app does
load_dotenv()

def check_env():
    print("🔍 Checking Environment Variables...")
    
    key = os.getenv('ELEVENLABS_API_KEY')
    if key:
        print(f"✅ ELEVENLABS_API_KEY found: {key[:5]}...{key[-5:]}")
        if KEY = os.getenv("ELEVENLABS_API_KEY"):
            print("   Matches expected key.")
        else:
            print("   ⚠️ Does NOT match expected key.")
    else:
        print("❌ ELEVENLABS_API_KEY NOT found in environment.")
        
    # Check current directory
    print(f"Current Directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")

if __name__ == "__main__":
    check_env()
