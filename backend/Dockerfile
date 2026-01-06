FROM python:3.12-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# API target
FROM base as api
EXPOSE 8000
CMD ["uvicorn", "app.entrypoints.http.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Worker target
FROM base as worker
CMD ["python", "-m", "app.entrypoints.workers.consumer"]
