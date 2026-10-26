# InternSync API image (Increment 1 design, Section 9; Increment 2 design, Section 10). The local demo and the
# reference deployment (a Hugging Face Space, port 7860) use the same image.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf PORT=8000 LOCAL_STORAGE_DIR=/data/storage
WORKDIR /app

COPY requirements.txt requirements-ai.txt ./
RUN pip install -r requirements.txt

# The embedding model (FR-MAT-01). WITH_AI=0 builds a smaller image that runs in basic matching mode (FR-MAT-04).
ARG WITH_AI=1
ARG EMBEDDING_MODEL=intfloat/multilingual-e5-small
RUN if [ "$WITH_AI" = "1" ]; then \
      pip install -r requirements-ai.txt && \
      python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('$EMBEDDING_MODEL')" && \
      chmod -R a+rX /opt/hf; \
    fi
# The model is baked in: never reach the Hugging Face Hub at run time.
ENV HF_HUB_OFFLINE=1 EMBEDDING_MODEL=$EMBEDDING_MODEL AI_ENABLED=$WITH_AI

COPY alembic.ini pyproject.toml ./
COPY alembic ./alembic
COPY app ./app

RUN useradd --create-home --uid 1000 internsync && mkdir -p /data/storage && chown internsync /data/storage
USER internsync

EXPOSE 8000 7860
# Migrate, load the reference data (idempotent), then serve on $PORT. Behind a proxy, set FORWARDED_ALLOW_IPS
# (read by uvicorn) so the registration limit sees the client address (docs/Deployment.md).
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
