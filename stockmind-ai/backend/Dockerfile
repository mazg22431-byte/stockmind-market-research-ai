FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed to build/consume scientific and ML packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    wget \
    ca-certificates \
    libsndfile1 \
    libgomp1 \
    libopenblas-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure pip, setuptools and wheel are up-to-date
RUN python -m pip install --upgrade pip setuptools wheel

COPY requirements.txt .

# Install Python dependencies. Attempt to install CPU wheels for torch first (helps avoid source builds),
# then install the rest of requirements. Using --prefer-binary and the official PyTorch CPU wheel index.
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir --prefer-binary torch -f https://download.pytorch.org/whl/cpu/torch_stable.html || true && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

EXPOSE 8000

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
