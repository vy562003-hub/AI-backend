# Stable Python (avoid 3.12+ issues)
FROM python:3.11-slim

# Environment config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for unstructured[pdf] + OCR
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy deps first (cache layer)
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Expose API port
EXPOSE 8000

# Run Flask with Gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8000", "--workers=2", "--timeout=180"]
