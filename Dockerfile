FROM python:3.10-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && \
    apt-get install -y git curl && \
    curl -Ls https://astral.sh/uv/install.sh | bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies using uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy project files
COPY . .

# Port exposed for Django dev server
EXPOSE 8000

# Default command
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]