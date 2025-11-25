import requests
import os

# Replace with the public URL generated from ngrok
NGROK_URL = "https://nonglutenous-erratically-glen.ngrok-free.dev/"  # Remove trailing slash

# Define paths
current_dir = os.getcwd()
json_file_path = os.path.join(current_dir, "story.json")
output_dir = os.path.join(current_dir, "audio_output")
output_audio_path = os.path.join(output_dir, "final_story.mp3")

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Send the JSON file to Colab
with open(json_file_path, 'rb') as f:
    response = requests.post(f"{NGROK_URL}/process_story", files={'file': f})

if response.status_code == 200:
    with open(output_audio_path, 'wb') as f:
        f.write(response.content)
    print(f"Audio file received and saved as {output_audio_path}")
else:
    print(f"Error: {response.status_code}")
    try:
        print(f"Error details: {response.json()}")
    except:
        print(f"Error message: {response.text}")