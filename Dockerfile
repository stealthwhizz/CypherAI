# CypherAI Docker Container
# Nothing fancy - just Python 3.11 with our dependencies

FROM python:3.11-slim

WORKDIR /app

# Install what we need (git for package installs, curl for health checks)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our code
COPY . .

# Make directories for logs and reports
RUN mkdir -p logs reports config

# Cloud Run needs us to listen on port 8080
EXPOSE 8080

# Basic health check - if this fails, container restarts
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the webhook server
CMD ["python", "webhook_server.py"]
