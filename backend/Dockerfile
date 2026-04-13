FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2 \
    PORT=7860

WORKDIR /app

# Install system deps (updated package names for Debian Trixie)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better Docker caching)
COPY requirements.txt .

# Install Python deps (CPU-only torch to save space/time)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security (optional but recommended)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run with single worker + CPU-optimized settings
CMD ["sh", "-c", "python -c \"import torch; torch.set_num_threads(2)\" && \
     uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]