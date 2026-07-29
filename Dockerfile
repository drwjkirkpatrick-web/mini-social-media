# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

# Security: non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy dependency file first for layer caching
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY app.py database.py blockchain.py auth.py config.py feed.py uploads.py moderation.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY data/ ./data/

# Ensure data directory exists and is writable
RUN mkdir -p /app/data /app/static/uploads && chown -R appuser:appgroup /app

USER appuser

EXPOSE 9197

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9197/health')" || exit 1

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:9197", "--preload", "--timeout", "30", "--keep-alive", "5", "app:app"]
