# KubeServe Base Inference Image
# Pre-installs common ML dependencies to reduce cold start time from 45s -> 3s
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies (minimal for healthcheck)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy base requirements and install common packages
# These are pre-installed because 90% of models use them
COPY requirements-base.txt /tmp/requirements-base.txt
RUN pip install --no-cache-dir -r /tmp/requirements-base.txt

# Copy application files
COPY main.py /app/main.py
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create model directory (will be mounted from init container)
RUN mkdir -p /model && chown -R appuser:appuser /app /model

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 80

# Health check endpoint (using Python since curl may not be available in slim image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:80/health')" || exit 1

# Use start.sh as entrypoint
ENTRYPOINT ["/app/start.sh"]

