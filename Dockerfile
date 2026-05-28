# ─── Builder stage ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install core dependencies
COPY pyproject.toml README.md ./
COPY clearcut/ clearcut/
RUN pip install --no-cache-dir .

# ─── Runtime stage ──────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/clearcut /usr/local/bin/clearcut

ENTRYPOINT ["clearcut"]
CMD ["--help"]
