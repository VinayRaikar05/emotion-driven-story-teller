import os

def check_env_file():
    print("🔍 Inspecting backend/.env content...")
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith('ELEVENLABS_API_KEY'):
                    key_value = line.split('=', 1)[1].strip()
                    print(f"Line {i+1}: ELEVENLABS_API_KEY={key_value[:5]}...{key_value[-5:] if len(key_value)>10 else ''}")
                    if key_value.startswith('your_'):
                        print("⚠️ WARNING: Key appears to be the placeholder!")
                    elif key_value.startswith('sk_'):
                        print("✅ Key appears to be a valid format.")
                    else:
                        print(f"⚠️ Unknown format: {key_value}")
    except FileNotFoundError:
        print("❌ .env file NOT found in current directory.")
        print(f"Current dir: {os.getcwd()}")
        print(f"Files: {os.listdir('.')}")

if __name__ == "__main__":
    check_env_file()
