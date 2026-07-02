# =============================================================================
# Hybrid AI Agent — Dockerfile
# =============================================================================
#
# BUILD  :  docker build -t hybrid-ai-agent .
# RUN    :  docker compose up          (preferred — handles volumes & .env)
#
# Base image choice: python:3.11-slim
#   - "slim" = minimal Debian, ~130 MB  vs  ~900 MB for the full image
#   - All our packages (torch, chromadb, sentence-transformers) have pre-built
#     binary wheels (manylinux), so they install fine on slim without needing
#     a compiler.  Alpine is smaller but breaks binary wheels.
# =============================================================================

FROM python:3.11-slim

# ── Working directory ─────────────────────────────────────────────────────────
# All subsequent COPY / RUN / CMD paths are relative to /app inside the image.
WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
# sqlite3  : needed by Python's built-in sqlite3 module at runtime
# curl     : useful for healthcheck probes in a compose stack
# --no-install-recommends keeps the image slim; clean up apt cache afterwards
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        sqlite3 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy only requirements.txt first.
# Docker builds layer-by-layer. If only our source code changes, this layer
# is cached and pip install does NOT re-run — much faster rebuilds.
COPY requirements.txt .

# Step 1: Install CPU-only PyTorch FIRST, before the rest of requirements.txt.
#
# Why: sentence-transformers and FlagEmbedding pull in torch as a dependency.
# Without this, pip installs the default torch which includes full CUDA support
# (~2 GB of NVIDIA libraries). That GPU code is useless inside a Docker container
# on a standard host — the container doesn't have GPU access.
#
# The CPU wheel is ~200 MB vs ~2 GB for the CUDA wheel.
# This single line cuts the build time by ~10 minutes and image size by ~4 GB.
#
# --extra-index-url tells pip to also look at PyTorch's own package index,
# which hosts the CPU-only wheels separately from PyPI.
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host download.pytorch.org \
    torch==2.3.1+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Step 2: Install everything else. Pip sees torch is already installed and
# won't try to reinstall or upgrade it, keeping the CPU-only version.
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
# Copy everything else after pip install so code changes don't bust the cache.
# .dockerignore excludes: venv/, data/, __pycache__/, .env, .git/
COPY . .

# ── Runtime port ──────────────────────────────────────────────────────────────
# EXPOSE documents the port; docker compose maps host:container in ports:
EXPOSE 8501

# ── Healthcheck ───────────────────────────────────────────────────────────────
# Docker will mark the container "healthy" once Streamlit responds on 8501.
# Useful in compose stacks where other services wait for this one.
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── Default command ───────────────────────────────────────────────────────────
# --server.headless true  : disables the browser-open popup (no desktop in Docker)
# --server.address 0.0.0.0: binds to all interfaces so the host can reach it
#                           (default is 127.0.0.1, which is unreachable from outside)
CMD ["streamlit", "run", "app/ui/main.py", \
     "--server.headless", "true", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501"]
