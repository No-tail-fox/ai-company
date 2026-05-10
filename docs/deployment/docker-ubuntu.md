# Docker Ubuntu Deployment

This project can run as a two-container stack:

- `backend`: FastAPI + SQLite + persistent storage
- `frontend`: Nginx serving the Vue build and proxying `/api` and `/storage`

## Prerequisites

- Ubuntu 22.04 or 24.04
- Docker Engine
- Docker Compose plugin

## Quick Start

```bash
git clone https://github.com/No-tail-fox/ai-company.git
cd ai-company
cp .env.example .env
sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$(openssl rand -hex 32)/" .env
docker compose up -d --build
```

The app will be available on `http://<server-ip>/`.

## Environment

Set values in `.env` before first start:

`JWT_SECRET` should be a long random value.
`PUBLIC_HTTP_PORT` defaults to `80`; use `8080` or another port if something is already using port 80.

## Data

Persistent data is stored in named volumes:

- `ai-company-backend-data` for `sqlite` database files
- `ai-company-backend-storage` for uploads and generated files

## Health Checks

Backend health:

```bash
curl http://<server-ip>/api/v1/health
```

## Common Operations

```bash
docker compose logs -f
docker compose restart backend
docker compose down
docker compose up -d --build
```
