# Kleinanzeigen Notifier API

Automatische Benachrichtigungs-App für kleinanzeigen.de mit Scraper, Token-System und Background Worker.

## Technologien
- FastAPI + Uvicorn
- PostgreSQL + SQLAlchemy
- APScheduler (Background Tasks)
- Docker + Docker Compose
- Render.com Deployment

## Schnellstart

```bash
cp .env.example .env
docker compose up --build
