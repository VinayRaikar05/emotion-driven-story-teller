# 🚀 Simple Deployment Guide

This guide connects your **GitHub Repository** to **Hugging Face** and **Vercel**. 
Once set up, every time you push code to GitHub, your app updates automatically.

---

## Part 1: Backend Deployment (Hugging Face)

**Goal**: Setup a Space and connect it to GitHub.

1.  **Create a Hugging Face Space**:
    *   Go to [huggingface.co/new-space](https://huggingface.co/new-space).
    *   Name: `emotion-storyteller-backend` (or similar).
    *   SDK: **Docker**.
    *   Hardware: **Free (2 vCPU)**.
    *   Click **Create Space**.

2.  **Get Your Access Token**:
    *   Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
    *   Click **Create new token**.
    *   Permissions: **Write** (Repositories).
    *   Copy the token (starts with `hf_...`).

3.  **Connect GitHub to Hugging Face**:
    *   Go to your **GitHub Repository** -> **Settings** -> **Secrets and variables** -> **Actions**.
    *   Click **New repository secret**.
    *   Add these 3 secrets:
        1.  `HF_TOKEN`: (Paste the token you copied)
        2.  `HF_USERNAME`: (Your Hugging Face username)
        3.  `HF_SPACE_NAME`: (The name of your space, e.g., `emotion-storyteller-backend`)
    *   *I have already added the deployment script to your code. As soon as you add these secrets and push a change, it will deploy!*

4.  **Configure Backend Variables**:
    *   Go to your Hugging Face Space -> **Settings**.
    *   Scroll to **Variables and secrets**.
    *   **Secrets**: Add `ELEVENLABS_API_KEY`.
    *   **Variables**: Add `NO_REDIS` = `true`.
    *   **Variables**: Add `CORS_ORIGINS` = `*`.

---

## Part 2: Frontend Deployment (Vercel)

**Goal**: Host the webpage.

1.  **Import to Vercel**:
    *   Go to [vercel.com/new](https://vercel.com/new).
    *   Import your GitHub repository.

2.  **Configure Project**:
    *   **Framework**: Vite (should prevent auto-detection).
    *   **Root Directory**: Click Edit -> Select `frontend`.

3.  **Connect to Backend**:
    *   Expand **Environment Variables**.
    *   Key: `VITE_API_URL`
    *   Value: `https://YOUR-HF-SPACE-URL.hf.space` (Find this in your HF Space -> "Embed this space" -> Direct URL).
    *   *Note: Remove any trailing slash `/` from the URL.*

4.  **Deploy**:
    *   Click **Deploy**.

---

## 🎉 Done!
- Update code on your computer.
- `git push origin main`.
- Watch GitHub Actions tab to see it deploy to Hugging Face automatically.
- Vercel updates automatically too.
