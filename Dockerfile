FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Environment variables (override at runtime with --env-file .env)
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface

# Usage:
#   docker build -t gemma-abliteration .
#   docker run --gpus all --env-file .env -v $(pwd)/data:/app/data gemma-abliteration \
#     python scripts/02_run_inference.py --size e4b --condition abliterated
