# Dynamically Voice-Modulated Story Generation System 🚀

## Overview
The **Dynamically Voice-Modulated Story Generation System** is an AI-driven solution that converts text-based stories into immersive, emotion-rich voice narrations. 

By leveraging advanced machine learning techniques and a microservices-based architecture, this system dynamically assigns unique voices to characters and modulates tone based on detected emotions, enhancing storytelling realism and engagement.

## Problem Statement

### 1. Background & Motivation
Traditional audiobook and story narration systems lack dynamic voice modulation, resulting in a flat, non-interactive experience. Most existing text-to-speech (TTS) systems face the following challenges:  

- **Lack of Emotional Depth** – Robotic voices without dynamic modulation.  
- **Generic Voice Output** – No character-specific or gender-based speech patterns.  
- **Poor Audio Quality** – Abrupt tone changes and unnatural pauses.  
- **Scalability Issues** – Monolithic systems struggle with multi-character dialogues.

### 2. Solution Approach

To overcome these challenges, this system: 
- **Story Input** – Accepts user-provided or AI-generated stories.  
- **Character Analysis** – Detects character genders and emotions using AI models.  
- **Voice Generation** – Produces character-specific, emotion-driven voices with Eleven Labs' TTS API.  
- **Audio Fine-Tuning** – Enhances transitions using Librosa & FFmpeg.  
- **Final Output** – Delivers high-quality, dynamically modulated audiobooks.

## System Architecture
<img src="Image/arching.jpeg"/>

### 1. Input Handling

📌 Users upload a script (PDF/Text) or generate a story using AI.

### 2. Backend Controller (Orchestration Layer)

✅ Manages requests and forwards text to processing microservices

✅ Collects processed data and structures it into JSON format

✅ Sends enriched text data to the voice generation service

### 3. Processing Microservices

📍 **Gender Detection Service** - Identifies character genders using an ML model

📍 **Emotion Detection Service** - Uses a fine-tuned RoBERTa model to detect emotions (e.g., happy, sad, angry, neutral, etc.)

### 4. Voice Generation Service

🎤 Generates character-specific, emotion-driven speech using **Eleven Labs' TTS API**

🎧 Produces high-quality `.wav` files with natural modulation

### 5. Audio Processing & Fine-Tuning

🎛 Uses **Librosa & FFmpeg** to:

✅ Adjust pitch and tone for natural transitions

✅ Merge multiple audio tracks for seamless storytelling



### 6. Final Story Output

🎬 Outputs an AI-generated audiobook featuring:

✅ Emotionally engaging and gender-accurate voices

✅ Dynamic voice modulation per character and emotion

✅ Professionally merged and high-quality narration



## Key Features

✔️ **Story Generation** – AI-generated storytelling option

✔️ **PDF/Text Extraction & Processing** – Accepts multiple formats

✔️ **Multi-Character Voice Assignment** – Assigns unique voices per character

✔️ **Gender Detection** – Determines if a character is male or female

✔️ **Emotion Detection** – Identifies emotions in dialogues

✔️ **Emotion-Driven Voice Modulation** – Adjusts voice tone dynamically

✔️ **Automated Story Processing** – Fully AI-driven pipeline


## Future Scope & Business Viability

### 🌟 Future Enhancements

- **Real-time voice adaptation** using reinforcement learning

- **User-controlled emotion intensity** customization

- **Multilingual support** for global reach

- **Interactive storytelling** integration for gaming & VR

- **AI-powered dubbing & audiobooks** for content creators

### 💰 Business Viability

- **Subscription-based SaaS model** (Pay-per-story or tiered access)

- **API-based monetization** for developers & businesses

- **Enterprise solutions** for media houses, publishers, and game studios



## Tech Stack

- **Machine Learning**:j-hartmann/emotion-english-distilroberta-base (Emotion Detection), Custom ML Model (Gender Detection),Transformers

- **TTS API**: Eleven Labs

- **Audio Processing**: Librosa, FFmpeg

- **Backend**: Python (FastAPI), Microservices Architecture

- **frontend**: react-vite

-**Libraries**:whisper, spacy, torchtransformers, ffmpeg

## Contribution Guidelines

1. Fork the repository

2. Create a new feature branch (`feature-xyz`)

3. Commit your changes (`git commit -m 'Added feature XYZ'`)

4. Push to the branch (`git push origin feature-xyz`)

5. Create a pull request for review

## License

This project is licensed under the **MIT License**.

## Contact

For queries and contributions, reach out via [email/contact link].

🚀 **Revolutionizing Storytelling with AI-Powered Voice Modulation!** 🎙️

