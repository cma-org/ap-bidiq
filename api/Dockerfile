FROM python:3.12-slim

WORKDIR /app

# System deps for cffi/cryptography + git for corpus fetch + tesseract/poppler for OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-tel \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast pip replacement)
RUN pip install --no-cache-dir uv

# Copy project metadata first for layer caching
COPY pyproject.toml ./
RUN uv pip install --system -e .

# Copy source
COPY app ./app

# Fetch the EPCC corpus from the public repo at build time (~1MB).
# Lives at /app/data/corpus so the auto-seed hook finds it.
ARG CORPUS_REF=main
RUN git clone --depth 1 --branch ${CORPUS_REF} https://github.com/cma-org/ap-bidiq.git /tmp/ap-bidiq \
    && mkdir -p ./data \
    && cp -r /tmp/ap-bidiq/data/corpus ./data/corpus \
    && rm -rf /tmp/ap-bidiq

# Render/Railway provide PORT
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
