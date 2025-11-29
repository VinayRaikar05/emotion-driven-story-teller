import os
from dotenv import load_dotenv

# Try to load .env as the app does
load_dotenv()

def check_env():
    print("🔍 Checking Environment Variables...")
    
    key = os.getenv('ELEVENLABS_API_KEY')
    if key:
        print(f"✅ ELEVENLABS_API_KEY found: {key[:5]}...{key[-5:]}")
        if key == "sk_e84c43552fbdeb61d35e4c86050632eec7801f74e572c46b":
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
