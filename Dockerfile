# =============================================================================
# Smart Agent Ledger — container image
#
# Runs the main dashboard/API process. Fleet collector nodes can run
# agent_ledger_server.py separately on trusted machines.
#
# 构建:  docker build -t smart-agent-ledger .
# Run (this machine only — publish on loopback and trust the Docker bridge):
#        docker run -d -p 127.0.0.1:8001:8001 \
#          -e SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE=1 \
#          -v "$PWD/data:/app/data" \
#          -v "$PWD/keys.env:/app/keys.env:ro" \
#          --name gateway smart-agent-ledger
# LAN / Fleet: publish with -p 8001:8001, set -e GATEWAY_API_KEY=your-secret,
#        and do NOT set SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE.
#
# The container listens on 0.0.0.0 internally (required for port publishing);
# access control is enforced by the published address and gateway auth.
# =============================================================================
FROM python:3.13-slim

# Minimal runtime dependency for the health check.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first to keep Docker layer caching effective.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source. Keep secrets and runtime files out via .dockerignore/.gitignore.
COPY . .

# Runtime config, logs, and events live in data/.
RUN mkdir -p data

EXPOSE 8001

# Health check for container orchestration.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -sf http://127.0.0.1:8001/health || exit 1

# Start the main API/dashboard process. 0.0.0.0 is the container-internal
# interface; restrict exposure with the published port (see above).
CMD ["python", "-m", "uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8001"]
