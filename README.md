# Kleinanzeigen Notifier API

Automatische Benachrichtigungs-App fuer kleinanzeigen.de mit echtem Scraper, Token-System und Background Worker.

## Technologien

- **FastAPI** + Uvicorn (async API)
- **PostgreSQL** + SQLAlchemy (async ORM)
- **APScheduler** (Background Worker)
- **httpx** + BeautifulSoup4 (Scraper)
- **Docker** + Docker Compose
- **Render.com** Deployment

---

## Schnellstart

```bash
cp .env.example .env
# .env mit deinen Zugangsdaten befuellen
docker compose up --build
```

API laeuft dann auf http://localhost:8000
Docs: http://localhost:8000/docs
Dashboard: http://localhost:8000/dashboard

---

## Architektur

```
.
├── app/
│   ├── main.py              # FastAPI App + /scrape + /dashboard
│   ├── config.py            # Settings via pydantic-settings
│   ├── core/
│   │   ├── database.py      # Async SQLAlchemy Engine + Session
│   │   └── scheduler.py     # APScheduler Setup
│   ├── models/
│   │   ├── search.py        # Search-Modell (SQLAlchemy)
│   │   ├── user.py          # User-Modell mit Token-Balance
│   │   └── token_transaction.py
│   ├── routers/
│   │   └── searches.py      # CRUD Endpoints fuer Suchen
│   ├── services/
│   │   ├── scraper_service.py   # Orchestriert Scrape + Token-Abbuchung
│   │   ├── token_service.py     # Token-Logik (deduct, refund)
│   │   └── webhook_service.py   # Sendet Ergebnisse per Webhook
│   └── utils/
│       └── url_generator.py     # Baut Kleinanzeigen-Such-URLs
├── scraper/
│   ├── scraper.py           # Echter Kleinanzeigen-Scraper (BeautifulSoup)
│   └── url_generator.py     # URL-Builder (auch standalone nutzbar)
├── worker.py                # Background Worker (laeuft separat)
├── Dockerfile
├── Dockerfile.worker
├── docker-compose.yaml
├── requirements.txt
└── .env.example
```

---

## API Endpunkte

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET |  | Health Check |
| GET |  | Einzelne URL scrapen |
| GET |  | Web-Dashboard |
| POST |  | Neue Suche anlegen |
| GET |  | Alle Suchen auflisten |
| GET |  | Einzelne Suche |
| POST |  | Suche pausieren |
| POST |  | Suche fortsetzen |
| DELETE |  | Suche loeschen |

Alle  Endpunkte benoetigen den Header .

---

## Umgebungsvariablen

Kopiere  nach  und fuell die Werte aus:

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
|  | PostgreSQL Verbindungs-URL |  |
|  | Passwort fuer lokale Docker DB |  |
|  | Min. Pause zwischen Requests (Sek.) |  |
|  | Max. Pause zwischen Requests (Sek.) |  |
|  | Timeout pro Request (Sek.) |  |

> **Wichtig:** Committe niemals deine echte  Datei! Sie ist in  ausgeschlossen.

---

## Token-System

Jeder User startet mit **20 Tokens**. Pro Scrape-Lauf wird 1 Token abgebucht.
Bei einem Fehler werden die Tokens automatisch zurueckerstattet.
Wenn ein User 0 Tokens hat, werden seine Suchen automatisch pausiert.

---

## Deployment auf Render.com

1. Repo auf GitHub pushen
2. Neuen **Web Service** auf render.com anlegen (API)
3. Neuen **Background Worker** anlegen (worker.py)
4. PostgreSQL Datenbank anlegen
5. Umgebungsvariablen im Render-Dashboard setzen

Die  Datei kann fuer automatisches Blueprint-Deployment genutzt werden.

---

## Bekannte Einschraenkungen

- Kleinanzeigen.de kann Anti-Bot-Massnahmen verscharfen — bei Problemen User-Agent rotieren
- Das Token-System hat kein echtes Auth (JWT) —  Header wird nicht verifiziert
- Kein Deduplication-System (bereits gesehene Anzeigen werden nicht gefiltert)

---

## Changelog (base44fix_suggestions Branch)

| Fix | Datei | Beschreibung |
|-----|-------|-------------|
| Echter Scraper |  | BeautifulSoup-basierter Kleinanzeigen-Scraper implementiert |
| Worker Bug |  | Scheduler-Scope-Bug gefixt, ORM statt Raw SQL |
| ORM Fix |  | Raw SQL durch SQLAlchemy ORM ersetzt, Ownership-Checks, GET+DELETE |
| Dependencies |  | Duplikate entfernt, Flask entfernt |
| Security |  | Aus Repo entfernt,  erstellt |
| Security |  | Neu erstellt, .env ausgeschlossen |
