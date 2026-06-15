import os

KEY = os.getenv("ELEVENLABS_API_KEY")

def fix_env():
    print("🔧 Fixing backend/.env...")
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        return

    with open(env_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    key_updated = False
    
    for line in lines:
        if line.strip().startswith('ELEVENLABS_API_KEY='):
            new_lines.append(f"ELEVENLABS_API_KEY={KEY}\n")
            key_updated = True
            print("✅ Replaced existing key.")
        else:
            new_lines.append(line)
            
    if not key_updated:
        new_lines.append(f"\nELEVENLABS_API_KEY={KEY}\n")
        print("✅ Appended new key.")

    with open(env_path, 'w') as f:
        f.writelines(new_lines)
        
    print("🎉 .env file updated successfully!")

if __name__ == "__main__":
    fix_env()
