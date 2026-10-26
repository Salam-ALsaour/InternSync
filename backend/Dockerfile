# InternSync API image (Increment 1 design, Section 9). Local demo and the free-tier deploy use the same image.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini pyproject.toml ./
COPY alembic ./alembic
COPY app ./app

RUN useradd --create-home --uid 1000 internsync && mkdir -p /data/storage && chown internsync /data/storage
USER internsync

EXPOSE 8000
# Migrate, load the reference data (idempotent), then serve.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
