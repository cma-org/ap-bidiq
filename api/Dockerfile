FROM python:3.12-slim

WORKDIR /app

# System deps for cffi/cryptography (needed by some transitive deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast pip replacement)
RUN pip install --no-cache-dir uv

# Copy project metadata first for layer caching
COPY pyproject.toml ./
RUN uv pip install --system -e .

# Copy source
COPY app ./app

# Bundle the corpus (so the seed step works inside the container)
COPY data ./data

# Render/Railway provide PORT
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
