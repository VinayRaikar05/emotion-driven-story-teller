FROM python:3.10-slim

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user . .

# Set Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Switch to the "user" user
USER user

# Expose port (Hugging Face Spaces defaults to 7860)
EXPOSE 7860

# Default command
CMD ["uvicorn", "models.api:app", "--host", "0.0.0.0", "--port", "7860"]
