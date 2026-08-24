# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    GRADIO_ANALYTICS_ENABLED=false \
    PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 user

USER user
WORKDIR /home/user/app
ENV PATH=/home/user/.local/bin:$PATH

COPY --chown=user requirements.txt .
RUN python -m pip install --user --upgrade pip && python -m pip install --user -r requirements.txt
COPY --chown=user . .
RUN python app.py --download-models

EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/',timeout=3)"
CMD ["python", "app.py"]
