#!/bin/bash
# Start RQ worker for processing TTS jobs
# This script should be run in the backend directory

echo "Starting RQ worker for TTS job processing..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set Python path to include backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start worker with scheduler support
# --with-scheduler: Enable scheduled jobs
# --burst: Exit after all jobs are processed (useful for testing)
rq worker tts --with-scheduler

# For production, use supervisor or systemd to manage the worker process
