# MyCousinVinyl

MyCousinVinyl is a dark-themed SPA for managing a personal vinyl collection. It is a React (Vite) frontend served by nginx and a FastAPI backend using hexagonal architecture, with Azure Entra ID authentication and group-based RBAC.

## Highlights

- Collection management for artists, albums, pressings, and collection items
- Discogs integration for search, metadata, and marketplace pricing
- Async integration via ActiveMQ (default) or MQTT with a transactional outbox
- Role-based access control (Admin > Editor > Viewer) enforced at HTTP entrypoints
- Docker-first local dev and NAS deployment

## Architecture at a glance

- **Frontend**: React SPA (Vite) + nginx
- **Backend**: FastAPI with hexagonal boundaries (domain / application / ports / adapters / entrypoints)
- **Database**: PostgreSQL (service-owned schema)
- **Message broker**: ActiveMQ or MQTT
- **Workers**: outbox processor, event consumer, pricing worker, cache cleanup, activity bridge
- **Discogs service**: standalone proxy for Discogs API calls

## Project layout

```
MyCousinVinyl/
  backend/                      # FastAPI app + workers
  discogs-service/              # Discogs proxy service
  frontend/                     # React SPA
  ha-addon/                     # Home Assistant add-on (single container)
  infrastructure/               # DB init and infra assets
  docs/                         # Installation and user guides
  scripts/                      # Helper scripts
  docker-compose.yml            # Local compose
  docker-compose.nas.yml        # NAS compose
  docker-compose.*.yml          # MQTT/ActiveMQ overrides
  .env.example                  # Environment template
  .env.nas                      # NAS env example
  deploy-to-local.ps1           # Local compose launcher
  deploy-to-nas.ps1             # NAS deployment script
```

## Requirements

- Docker Desktop or Docker Engine + Compose
- Node.js 20+
- Python 3.12+ (for local tooling/tests)
- Azure Entra ID tenant and app registration

## Quick start (local Docker)

1. Create the environment file:

```bash
cp .env.example .env
```

2. Set required values in `.env` (Azure, database, Discogs, broker).
3. Build and run:

```bash
docker compose up -d --build
```

Optional compose overrides:

```bash
# Use MQTT without ActiveMQ
docker compose -f docker-compose.yml -f docker-compose.mqtt.yml up -d --build

# Use external MQTT with internal Postgres
MQTT_URL=mqtt://<broker>:1883 \
docker compose -f docker-compose.yml -f docker-compose.external-mqtt.yml up -d --build
```

Services:

- Frontend: http://localhost:3000
- API: http://localhost:8000 (health: `GET /health`)
- Discogs service: http://localhost:8001 (health: `GET /health`)
- ActiveMQ UI: http://localhost:8161
- Postgres: localhost:5432

## Run services individually

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.entrypoints.http.main:app --reload
```

Workers (examples):

```bash
cd backend
python -m app.entrypoints.workers.outbox_processor
python -m app.entrypoints.workers.consumer
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Discogs service:

```bash
cd discogs-service
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## NAS deployment

Use the PowerShell script to deploy to a Synology NAS. It copies the project and runs `docker compose` on the NAS.

```powershell
$env:SYNOLOGY_USER = "your-username"
$env:SYNOLOGY_PASSWORD = "your-password"
$env:SYNOLOGY_HOST = "your-nas-host"  # optional

.\deploy-to-nas.ps1 -Build
```

The NAS compose file defaults to `docker-compose.nas.yml`. For MQTT variants, use the corresponding `docker-compose.nas.*.yml` override.

## Documentation

- `docs/installation-guide.md` for Docker install and environment setup
- `docs/users-guide.md` for UI walk-throughs
- `docs/application-architecture-development-design-guide.md` for architecture and design details
- `docs/home-assistant-addon.md` for the HA add-on

## Contributing notes

- Keep security checks at HTTP entrypoints; domain and application layers stay auth-agnostic.
- Scope collection operations by `user_id`.
- Prefer focused UI changes using modals and table actions.

## License

AGPL-3.0. See `LICENSE`.
