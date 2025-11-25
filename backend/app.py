from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/generate-story', methods=['POST'])
def generate_story():
    # Placeholder for story generation logic
    data = request.json  # Ensure the server can handle an empty or missing payload
    return jsonify({"story": "Generated story will appear here"})

@app.route('/extract-info', methods=['POST'])
def extract_info():
    data = request.json
    text = data.get('text', '')

    # Placeholder for extraction logic
    extracted_info = {
        "gender": "detected gender",
        "name": "detected name",
        "phrases": ["phrase 1", "phrase 2"]
    }
    return jsonify(extracted_info)

@app.route('/detect-emotion', methods=['POST'])
def detect_emotion():
    data = request.json
    text = data.get('text', '')

    # Placeholder for emotion detection logic
    emotions = {"emotion": "neutral"}
    return jsonify(emotions)

if __name__ == '__main__':
    app.run(debug=True)
