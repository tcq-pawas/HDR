FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpq5 \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Create non-root user for runtime (entrypoint starts as root to fix volume perms)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/media /app/staticfiles /app/static && \
    chown -R appuser:appuser /app

# Do NOT switch USER here — entrypoint must run as root to chown mounted volumes,
# then drops privileges to appuser before starting Gunicorn.
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
