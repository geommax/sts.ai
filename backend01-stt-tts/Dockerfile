
FROM ubuntu:22.04

# Install system dependencies and Python (robustly)
ENV DEBIAN_FRONTEND=noninteractive
RUN set -eux; \
    # retry apt-get update once if it fails due to transient network issues
    apt-get update || (sleep 5 && apt-get update); \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        apt-transport-https \
        gnupg \
        dirmngr \
        wget \
        curl \
        git \
        build-essential \
        ffmpeg \
        python3 \
        python3-pip \
        python3-venv \
        unzip; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Download Vosk model (small English)
RUN mkdir -p /app/ && \
    wget -O /app/vosk-model-small-en-us-0.15.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip /app/vosk-model-small-en-us-0.15.zip -d /app/vosk-model-small-en-us-0.15 && \
    rm -rf /app/vosk-model-small-en-us-0.15.zip

# Install Piper (TTS) from PyPI
RUN pip3 install --no-cache-dir piper-tts
# Download Piper model using the official CLI
RUN mkdir -p /app/piper_models && \
    cd /app/piper_models && \
    python3 -m piper.download_voices en_US-lessac-medium

# Copy your source code
COPY src/ /app/src/

# Set environment variables for model paths
ENV VOSK_MODEL_PATH=/app/vosk-model-small-en-us-0.15
ENV PIPER_MODEL_PATH=/app/piper_models/en_US-lessac-medium.onnx
ENV PIPER_MODEL_CONFIG=/app/piper_models/en_US-lessac-medium.onnx.json

# Expose port (change if needed)
EXPOSE 5001

# Run the backend
CMD ["python3", "/app/src/app.py"]