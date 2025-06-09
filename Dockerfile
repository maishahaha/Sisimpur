# LLM-Optimized Dockerfile for SISIMPUR
# This Dockerfile creates a minimal image with LLM-based OCR (no EasyOCR/PyTorch)

FROM python:3.10-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Install minimal system dependencies for LLM-based processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        wget \
        poppler-utils \
        && \
    curl -Ls https://astral.sh/uv/install.sh | bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy LLM-optimized requirements
COPY requirements.txt .

# Install Python packages (no PyTorch/EasyOCR dependencies)
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make health check script executable
RUN chmod +x /app/healthcheck.py

# Create necessary directories
RUN mkdir -p /app/media/brain/temp_extracts && \
    mkdir -p /app/media/brain/qa_outputs && \
    mkdir -p /app/media/brain/uploads && \
    mkdir -p /app/staticfiles

# Expose Django dev server port
EXPOSE 8000

# Default command (can be overridden by docker-compose)
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]