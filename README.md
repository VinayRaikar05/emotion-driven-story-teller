# 🎙️ Emotion-Driven Storyteller

> **AI-Powered Audiobook Generation with Dynamic Voice Modulation**

A production-ready system that transforms text stories into immersive, emotion-rich audio experiences using advanced ML models and asynchronous job processing. Built as a portfolio project to demonstrate modern cloud-native architecture, robust error handling, and production best practices.

[![Backend CI/CD](https://github.com/VinayRaikar05/emotion-driven-story-teller/actions/workflows/backend-cicd.yml/badge.svg)](https://github.com/VinayRaikar05/emotion-driven-story-teller/actions/workflows/backend-cicd.yml)
[![Frontend CI/CD](https://github.com/VinayRaikar05/emotion-driven-story-teller/actions/workflows/frontend-cicd.yml/badge.svg)](https://github.com/VinayRaikar05/emotion-driven-story-teller/actions/workflows/frontend-cicd.yml)

---

## 🎯 What It Does

This application takes a story script (PDF or text), analyzes the emotions and genders of characters, then generates a fully voice-acted audiobook with:

- **Gender-Based Voice Assignment**: Unique voices for each character based on detected gender
- **Emotion-Driven Modulation**: Voice tone adjusts based on detected emotions (happy, sad, angry, etc.)
- **Asynchronous Processing**: Non-blocking job queue for handling long-running TTS operations
- **Cloud-Ready Architecture**: S3 storage, Redis queue, container-based deployment

**Demo Use Case**: Upload a story → System detects characters & emotions → Generates MP3 with multiple voices → Download and listen!

---

## 🏗️ Architecture

```
┌─────────┐      ┌──────────────┐      ┌─────────────┐ 
│ Browser │─────▶│ React        │─────▶│ FastAPI     │
│         │      │ Frontend     │      │ Backend     │
└─────────┘      └──────────────┘      └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
             ┌─────────────┐          ┌─────────────┐           ┌─────────────┐
             │ Gender      │          │ Emotion     │           │ Redis       │
             │ Detection   │          │ Detection   │           │ Queue       │
             │ (LSTM)      │          │ (RoBERTa)   │           └──────┬──────┘
             └─────────────┘          └─────────────┘                  │
                                                                        ▼
                                                                 ┌─────────────┐
                                                                 │ RQ Worker   │
                                                                 └──────┬──────┘
                                                                        │
                    ┌───────────────────────────────────────────────────┼────────┐
                    │                                                   │        │
                    ▼                                                   ▼        ▼
             ┌─────────────┐                                    ┌─────────────┐ │
             │ ElevenLabs  │                                    │ S3/MinIO    │ │
             │ TTS API     │                                    │ Storage     │ │
             └─────────────┘                                    └──────┬──────┘ │
                    │                                                   │        │
                    └───────────────────────────────────────────────────┴────────┘
                                              │
                                              ▼
                                        Presigned URL
                                              │
                                              ▼
                                        User Downloads MP3
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose**
- **ElevenLabs API Key** ([sign up](https://elevenlabs.io) - free tier available)
- **Git**

### One-Command Demo

```bash
# 1. Clone the repository
git clone https://github.com/VinayRaikar05/emotion-driven-story-teller.git
cd emotion-driven-story-teller

# 2. Set your ElevenLabs API key
echo "ELEVENLABS_API_KEY=your_key_here" > backend/.env

# 3. Start all services
docker-compose up --build

# 4. Open your browser
# Frontend: http://localhost:3000
# Backend API Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001
```

### Manual Testing (Without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn models.api:app --reload

# Frontend (separate terminal)
npm install
npm run dev

# Worker (separate terminal)
cd backend
./start-worker.sh
```

---

## 💡 Tech Stack & Design Decisions

| Component | Technology | Why? |
|-----------|------------|------|
| **Frontend** | React + Vite | Fast dev experience, modern tooling |
| **Backend** | FastAPI | Async-first, type-safe, auto-docs |
| **Job Queue** | RQ + Redis | Simple, Pythonic, perfect for TTS workloads |
| **TTS Engine** | ElevenLabs API | Production-grade voices, emotion support |
| **Gender Detection** | LSTM (TensorFlow) | Lightweight, trained on character names |
| **Emotion Detection** | RoBERTa (HuggingFace) | SOTA transformer model for sentiment |
| **Storage** | S3/MinIO | Durable, scalable, presigned URLs |
| **Containerization** | Docker Compose | Reproducible local dev environment |
| **CI/CD** | GitHub Actions | Automated testing & builds |
| **Monitoring** | Prometheus + Sentry | Metrics & error tracking |

### Why Async Job Queue?

TTS generation takes 10-60 seconds. **Blocking the HTTP request** would timeout and create terrible UX. Instead:
1. User uploads story → **Immediate 202 response** with `job_id`
2. Worker processes TTS in background
3. User polls `/jobs/{job_id}` → **Shows progress**
4. Worker uploads MP3 to S3 → **Returns presigned URL**
5. User downloads completed audio

**Interview Talking Point**: "This demonstrates understanding of asynchronous processing patterns essential for production systems."

### Why RQ over Celery?

- **Simplicity**: RQ is pure Python, zero config
- **Good Enough**: For TTS workloads (not millions of jobs/sec)
- **Easy Debugging**: Inspect jobs with `rq info`

**Trade-off**: Celery offers more features (cron, chaining) but adds complexity. For a portfolio project, RQ demonstrates the pattern without over-engineering.

---

## 📋 How to Demo (For Interviews)

**3-Minute Technical Demo Script**:

```bash
# 1. Show the architecture
"This is a microservices architecture with React frontend, FastAPI backend,
 async job processing with RQ, and cloud storage with S3."

# 2. Start services
docker-compose up

# 3. Upload a story (use story1.txt from repo)
"When I upload a PDF, the backend:
  - Extracts text using llama-index
  - Detects character genders with an LSTM model
  - Analyzes emotions using RoBERTa
  - Enqueues a TTS job"

# 4. Show async job processing
curl http://localhost:8000/jobs/{job_id}
"Notice the status: 'processing'. This is a background worker generating
 audio with ElevenLabs API. The request doesn't block."

# 5. Show completed job
"After 30-60 seconds, status becomes 'completed' with a presigned S3 URL.
 The audio is stored in MinIO (S3-compatible) with a 7-day lifecycle."

# 6. Discuss production readiness
"For production, I'd deploy:
  - Frontend on Vercel
  - Backend on Render/Cloud Run
  - Use AWS S3 instead of MinIO
  - Add Prometheus for metrics, Sentry for errors"
```

**Key Discussion Points**:
- **Retry logic**: TTS client has exponential backoff for rate limits
- **Circuit breaker**: Prevents cascading failures
- **Concurrency limiting**: Max 2 parallel ElevenLabs requests
- **Testing**: Unit tests for retry logic, mocked HuggingFace models
- **CI/CD**: Automated tests on every push, Docker build validation

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test
pytest tests/test_tts_client.py::test_retry_with_backoff -v
```

**Test Coverage Goals**: >70% coverage on backend core (jobs, TTS client, API endpoints)

---

## 📊 Deployment

### Completely Free Stack (Recommended)
This project is optimized for deployment on **Hugging Face Spaces** (Backend) and **Vercel** (Frontend).

👉 **[Read the Complete Free Deployment Guide](deployment_guide.md)**

---

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload-script` | Upload PDF, get dialogues with genders |
| `POST` | `/detect-emotions` | Add emotion analysis to dialogues |
| `POST` | `/generate-audio` | **Returns job_id** (async) |
| `GET` | `/jobs/{job_id}` | Poll job status, get download URL |
| `GET` | `/health` | Health check (for load balancers) |
| `GET` | `/metrics` | Prometheus metrics |

Full API documentation: `http://localhost:8000/docs` (FastAPI auto-generated Swagger UI)

---

## 🔒 Environment Variables

Copy `backend/.env.example` → `backend/.env` and configure:

```bash
ELEVENLABS_API_KEY=sk_...  # Required
REDIS_HOST=localhost
S3_ENDPOINT=http://localhost:9000  # Remove for AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

**Never commit `.env` to Git!**

---

## 🎓 What I Learned

This project demonstrates:
- ✅ **Async programming**: Job queues, workers, non-blocking APIs
- ✅ **Resilience patterns**: Retry logic, circuit breakers, backoff
- ✅ **Cloud-native**: S3 storage, containerization, 12-factor app
- ✅ **Testing**: Unit tests, mocking, coverage
- ✅ **CI/CD**: Automated testing, Docker builds
- ✅ **Production ops**: Logging, metrics, health checks

---

## 🚧 Known Limitations

- **Development vs Production**: Colab/ngrok option exists for dev but not recommended for production
- **No Database**: Job state stored in Redis (volatile). For production, add PostgreSQL for audit logs.
- **Single Worker**: Current setup runs 1 worker. For scale, run multiple workers on different machines.
- **No User Auth**: Public API. For production, add API keys or OAuth.
- **Audio Storage**: 7-day lifecycle. For permanent storage, adjust S3 lifecycle rules.

**Future Improvements**:
- Add user accounts and login
- Persist job history in database
- Support more TTS providers (Google Cloud TTS, Azure)
- Real-time progress updates via WebSockets
- Pre-signed upload URLs for large PDFs

---

## 📚 Additional Documentation

- [**Implementation Plan**](docs/IMPLEMENTATION.md) - Detailed architecture decisions
- [**Deployment Guide**](docs/DEPLOYMENT.md) - Cloud deployment instructions
- [**Colab Development**](docs/DEV_COLAB.md) - Using Google Colab for dev
- [**Demo Script**](docs/DEMO.md) - Interview presentation guide

---

## 🤝 Contributing

This is a portfolio project, but issues and PRs are welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---



