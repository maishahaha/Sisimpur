FROM python:3.10-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH" \
    EASY_OCR_MODEL_DIR=/root/.EasyOCR/model

# Set working directory
WORKDIR /app

# Install system dependencies, uv, wget, and unzip
RUN apt-get update && \
    apt-get install -y git curl wget unzip libgl1 libglib2.0-0 && \
    curl -Ls https://astral.sh/uv/install.sh | bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Download and extract EasyOCR models
RUN mkdir -p $EASY_OCR_MODEL_DIR && \
    wget https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip && \
    wget https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip && \
    unzip english_g2.zip -d $EASY_OCR_MODEL_DIR && \
    unzip craft_mlt_25k.zip -d $EASY_OCR_MODEL_DIR && \
    rm english_g2.zip craft_mlt_25k.zip

# Copy the rest of the application code
COPY . .

# Expose Django dev server port
EXPOSE 8000

# Start the development server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]