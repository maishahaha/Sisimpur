# CPU-Optimized Dockerfile for SISIMPUR
# This Dockerfile creates a minimal image with CPU-only EasyOCR

FROM python:3.10-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH" \
    EASY_OCR_MODEL_DIR=/root/.EasyOCR/model \
    TORCH_HOME=/tmp/torch \
    TRANSFORMERS_CACHE=/tmp/transformers

# Set working directory
WORKDIR /app

# Install minimal system dependencies for CPU-only EasyOCR
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        wget \
        unzip \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libgcc-s1 \
        poppler-utils \
        && \
    curl -Ls https://astral.sh/uv/install.sh | bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy CPU-optimized requirements
COPY requirements.txt .

# Install Python packages with CPU-only PyTorch
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Note: EasyOCR models will be downloaded automatically on first use
# This keeps the image size smaller and allows for dynamic model loading

# Copy the rest of the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/media/brain/temp_extracts && \
    mkdir -p /app/media/brain/qa_outputs && \
    mkdir -p /app/media/brain/uploads && \
    mkdir -p /app/staticfiles

# Expose Django dev server port
EXPOSE 8000

# Default command (can be overridden by docker-compose)
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]