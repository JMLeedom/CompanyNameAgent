# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Keep Python logs visible and make the src-layout package importable.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    HOME=/home/appuser

WORKDIR /app

# libgomp1 is required by some scientific Python wheels at runtime.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies before copying application code so Docker can reuse
# this layer whenever the source changes but requirements.txt does not.
COPY requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install --requirement requirements.txt

# Run the application as an unprivileged user.
RUN groupadd --system appgroup \
    && useradd --system --create-home --gid appgroup appuser

COPY --chown=appuser:appgroup app.py ./app.py
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup tools/ ./tools/
COPY --chown=appuser:appgroup data/ ./data/

USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/', timeout=3)" || exit 1

CMD ["python", "app.py"]
