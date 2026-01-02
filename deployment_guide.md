# � Simple & Free Deployment Guide

Deploy your **Emotion-Driven Storyteller** for free in less than 15 minutes.

This simplified setup uses:
- **Backend**: Hugging Face Spaces (Free CPU Basic)
- **Frontend**: Vercel (Free Static Hosting)
- **Process**: Synchronous generation (No Redis or S3 required!)

---

## 🛠️ Prerequisites
1. **GitHub Account**: [Sign up](https://github.com/)
2. **Hugging Face Account**: [Sign up](https://huggingface.co/join)
3. **Vercel Account**: [Sign up](https://vercel.com/signup)
4. **ElevenLabs API Key**: [Get it here](https://elevenlabs.io/) (Click Profile -> API Key)

---

## Part 1: Backend Deployment (Hugging Face)

1. **Create a Space**:
    - Go to [huggingface.co/new-space](https://huggingface.co/new-space).
    - **Space Name**: `emotion-storyteller-backend`.
    - **License**: `MIT`.
    - **SDK**: `Docker`.
    - **Hardware**: `Cpu basic (2 vCPU · 16GB · FREE)`.
    - Click **Create Space**.

2. **Upload Code (Git Push Method)**:
    - **Option A: Direct Git Push (Easiest)**
        1. On your local machine, navigate to your `backend` folder:
           ```bash
           cd backend
           ```
        2. Initialize git (if not already): `git init`
        3. Add your Hugging Face Space as a remote:
           ```bash
           git remote add space https://huggingface.co/spaces/YOUR_USERNAME/emotion-storyteller-backend
           ```
        4. Force push your code:
           ```bash
           git add .
           git commit -m "Deploy backend"
           git push -f space master:main
           ```
           *(Note: You'll be asked for your HF Username and Password. For password, use an **Access Token** with 'write' permissions from your HF Settings).*

    - **Option B: Connect GitHub Repo**:
        1. Push your code to a generic GitHub repository first.
        2. In your Hugging Face Space, go to **Settings** -> **Git Repository** -> **Connect/Sync with GitHub**.
        3. Authorize and select your repo.

3. **Configure Environment Variables**:
    - Click the **Settings** tab.
    - Scroll to **Variables and secrets**.
    - Add the following **Secrets** (Private):
        - `ELEVENLABS_API_KEY`: `(Paste your actual key)`
    - Add the following **Variables** (Public):
        - `NO_REDIS`: `true` (This enables the simple mode without S3/Redis)
        - `CORS_ORIGINS`: `*` (Allows access from any frontend for simplicity)

4. **Wait for Build**:
    - Click the **App** tab. You will see "Building".
    - Wait ~3-5 minutes. When it says "Running", copy the **Direct URL**.
    - *Tip*: Click the "Embed this space" menu (top right) -> Copy **Direct URL**. It looks like: `https://username-space-name.hf.space`.

---

## Part 2: Frontend Deployment (Vercel)

1. **Push Code to GitHub**:
    - If you haven't already, push your code to your own GitHub repository.

2. **Import to Vercel**:
    - Go to [vercel.com/new](https://vercel.com/new).
    - Under "Import Git Repository", find your repo and click **Import**.

3. **Configure Building**:
    - **Framework Preset**: `Vite`.
    - **Root Directory**: Click "Edit" and select `frontend`.

4. **Add Environment Variable**:
    - Expand **Environment Variables**.
    - Key: `VITE_API_URL`
    - Value: `https://YOUR-HF-SPACE-URL.hf.space` (The URL you copied in Part 1).
    - *Important*: Do NOT include a trailing slash `/`.

5. **Deploy**:
    - Click **Deploy**.
    - Wait ~1 minute. When fireworks appear, click the preview image to visit your live site!

---

## 🎉 Done!
Your app is now live.

### How it works in this mode:
- When you click "Generate Audio", the request goes to your HF Backend.
- The backend processes the story ensuring the "Playlist Mode" is active.
- Audio is returned directly to your browser for playback.
- **Note on Free Tier**: The generation makes a long request (30-60s). If it times out, retry with a shorter story segment.
