# Installation Guide

## Purpose

This guide describes how to install, configure, and operate the application in Docker.

## 1. Installation

### Choice of host

- Local development: Docker Desktop on Windows/macOS/Linux.
- Dedicated server/NAS: Docker Engine + Docker Compose.
- Home Assistant add-on: separate add-on repo (single container), if needed.

### docker-compose.yml overview

`docker-compose.yml` defines the main services:

- `frontend`: React SPA served by nginx (port 3000).
- `api`: FastAPI backend (port 8000).
- `discogs-service`: Discogs proxy service (port 8001).
- `postgres`: PostgreSQL database (port 5432).
- `activemq`: ActiveMQ broker (port 8161 UI, 61613 STOMP).
- `outbox-processor`: publishes outbox events.
- `worker`: event consumer.
- `pricing-worker`: Discogs marketplace pricing updates.
- `cache-cleanup`: Discogs cache cleanup.
- `activity-bridge`: forwards activity events to API websocket.

### Environment configuration (.env)

Create `.env` from `.env.example` and set:

Database:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`

Messaging:
- `MESSAGE_BROKER` (`activemq` or `mqtt`)
- `MQTT_URL`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `MQTT_TOPIC_PREFIX`
- `ACTIVEMQ_URL`, `ACTIVITY_TOPIC`, `ACTIVITY_BRIDGE_URL`, `ACTIVITY_BRIDGE_TOKEN`

Azure Entra ID:
- `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_AUDIENCE`
- `AZURE_GROUP_ADMIN`, `AZURE_GROUP_EDITOR`, `AZURE_GROUP_VIEWER`

Discogs:
- `DISCOGS_USER_AGENT`, `DISCOGS_KEY`, `DISCOGS_SECRET`
- `DISCOGS_OAUTH_TOKEN`, `DISCOGS_OAUTH_TOKEN_SECRET` (OAuth 1.0a)
- `DISCOGS_OAUTH_CALLBACK_URL`, `DISCOGS_OAUTH_AUTHORIZE_URL`, `DISCOGS_OAUTH_API_BASE_URL`

Frontend:
- `VITE_API_URL`, `VITE_AZURE_CLIENT_ID`, `VITE_AZURE_TENANT_ID`, `VITE_AZURE_REDIRECT_URI`

### Connecting to Discogs

1. Set `DISCOGS_USER_AGENT`, `DISCOGS_KEY`, `DISCOGS_SECRET`.
2. For marketplace pricing, set either:
   - Personal access token: `DISCOGS_OAUTH_TOKEN` only, or
   - OAuth 1.0a: `DISCOGS_OAUTH_TOKEN` + `DISCOGS_OAUTH_TOKEN_SECRET`.
3. For user collection sync, use the OAuth flow exposed by the API.

### Ports

- Frontend: `3000`
- API: `8000`
- Discogs service: `8001`
- PostgreSQL: `5432`
- ActiveMQ Admin UI: `8161`

### Deploy, build, run, and monitor

Build and run everything:

```bash
docker compose up -d --build
```

Use MQTT without ActiveMQ:

```bash
docker compose -f docker-compose.yml -f docker-compose.mqtt.yml up -d --build
```

Use external MQTT with internal Postgres:

```bash
MQTT_URL=mqtt://<broker>:1883 \
docker compose -f docker-compose.yml -f docker-compose.external-mqtt.yml up -d --build
```

View logs:

```bash
docker compose logs -f api
```

## 2. Daily Operation

### PostgreSQL Backup and Restore

Backup:

```bash
docker compose exec postgres pg_dump -U postgres -d mycousinvinyl > backup.sql
```

Restore:

```bash
cat backup.sql | docker compose exec -T postgres psql -U postgres -d mycousinvinyl
```

### Liveness probes

Use HTTP health endpoints:

- API: `GET /health` on port 8000
- Discogs service: `GET /health` on port 8001

You can wire these into your monitoring system or reverse proxy health checks.
