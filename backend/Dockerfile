FROM python:3.11-slim

WORKDIR /app

# Install dependencies needed for compiling certain python packages
RUN apt-get update && apt-get install -y gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Use no-cache to keep image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run Uvicorn specifically importing from app module 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
