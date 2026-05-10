FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_URL=sqlite:////data/app.db \
    STORAGE_DIR=/storage

WORKDIR /app/backend

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /data /storage \
    && chown -R app:app /app /data /storage

COPY backend/requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

COPY backend/app ./app

RUN chown -R app:app /app/backend

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
