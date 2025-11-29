import subprocess
import os
import signal
import sys

def handler(signum, frame):
    print("Shutting down services...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handler)
signal.signal(signal.SIGINT, handler)

redis_url = os.environ.get("REDIS_URL")
if not redis_url:
    print("Error: REDIS_URL not set")
    sys.exit(1)

print("Starting RQ Worker...")
worker = subprocess.Popen(["rq", "worker", "tts", "--url", redis_url])

print("Starting FastAPI...")
api = subprocess.Popen(["uvicorn", "models.api:app", "--host", "0.0.0.0", "--port", os.environ.get("PORT", "10000")])

# Wait for API to finish (it shouldn't unless crashed or stopped)
api.wait()

# Cleanup
worker.terminate()
