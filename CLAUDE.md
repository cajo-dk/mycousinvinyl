# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyCousinVinyl is a vinyl record collection management application implementing **Hexagonal Architecture** with:
- **Frontend**: React SPA with Azure Entra ID authentication (MSAL)
- **Backend**: Python FastAPI with hexagonal/ports-and-adapters architecture
- **Discogs Service**: Standalone Python service for Discogs API integration
- **Database**: PostgreSQL with transactional outbox pattern
- **Message Broker**: Apache ActiveMQ for async integration
- **Deployment**: Docker containers on Synology NAS (10.254.1.210)

## Essential Commands

### Local Development

Start all services:
```bash
docker compose up -d
```

Stop all services:
```bash
docker compose down
```

View logs:
```bash
docker compose logs -f [service-name]
# service-name: frontend, api, worker, outbox-processor, activity-bridge, discogs-service, postgres, activemq
```

### Backend Development

Run API server locally:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.entrypoints.http.main:app --reload
```

Run worker locally:
```bash
cd backend
python -m app.entrypoints.workers.consumer
```

Run tests:
```bash
cd backend
pytest                    # Run all tests
pytest tests/unit         # Run only unit tests
pytest tests/integration  # Run only integration tests
pytest -m unit            # Run tests marked as unit
pytest -m integration     # Run tests marked as integration
pytest --cov=app --cov-report=html  # Run with coverage report
```

Format and lint:
```bash
cd backend
black .
ruff check .
mypy .
```

### Frontend Development

Run dev server:
```bash
cd frontend
npm install
npm run dev
```

Build production:
```bash
cd frontend
npm run build
```

Lint:
```bash
cd frontend
npm run lint
```

### Deployment to Synology NAS

Windows (PowerShell):
```powershell
$env:SYNOLOGY_USER = "your-username"
$env:SYNOLOGY_PASSWORD = "your-password"
.\deploy-to-nas.ps1 -Build
```

The deployment script will:
1. Build Docker images (if -Build flag is specified)
2. Copy docker-compose.nas.yml and .env.nas to the NAS
3. SSH into the NAS and deploy using docker compose
4. Use either PuTTY (plink/pscp) or OpenSSH for file transfer and commands

## Architecture Principles

### Hexagonal Architecture (Ports and Adapters)

The backend strictly follows hexagonal architecture with clear separation of concerns:

```
backend/app/
├── domain/              # Business entities and domain logic (pure Python, no dependencies)
├── application/         # Use cases and business orchestration
│   ├── ports/          # Interface contracts (Repository, UnitOfWork, MessagePublisher)
│   └── services/       # Application services implementing use cases
├── adapters/           # Infrastructure implementations
│   ├── postgres/       # Database adapter (SQLAlchemy)
│   └── activemq/       # Message broker adapter (STOMP)
└── entrypoints/        # External interfaces
    ├── http/           # REST API (FastAPI) - enforces auth/authz
    └── workers/        # Message queue consumers
        ├── consumer.py           # Event consumer worker
        ├── outbox_processor.py   # Outbox pattern worker
        └── activity_ws_bridge.py # WebSocket activity bridge
```

**Dependency Rule**: Dependencies point inward. Domain has no dependencies. Application depends on domain. Adapters and entrypoints depend on application/domain.

### Security Architecture

**Authentication and authorization are enforced ONLY at entrypoint boundaries:**

1. **HTTP Entrypoints** ([backend/app/entrypoints/http/auth.py](backend/app/entrypoints/http/auth.py)):
   - Validate Azure Entra ID JWT tokens
   - Extract user information and group claims
   - Enforce group-based authorization using dependency injection

2. **Domain and Application Layers**:
   - Completely security-agnostic
   - No knowledge of authentication mechanisms
   - No authorization checks
   - Pure business logic only

3. **Worker Entrypoints**:
   - Process events from message queue
   - Do NOT execute user-privileged operations requiring authorization
   - If workers need authorization, implement at worker entrypoint level

**Key Files:**
- [backend/app/entrypoints/http/auth.py](backend/app/entrypoints/http/auth.py) - Token validation, User model, authorization dependencies
- [backend/app/config.py](backend/app/config.py) - Azure Entra ID configuration
- [frontend/src/auth/authConfig.ts](frontend/src/auth/authConfig.ts) - MSAL configuration
- [frontend/src/api/client.ts](frontend/src/api/client.ts) - Axios client with automatic token injection

### Azure Entra ID Integration

**Token Validation** ([backend/app/entrypoints/http/auth.py](backend/app/entrypoints/http/auth.py:41-107)):
- Validates JWT signature using Azure's JWKS endpoint
- Accepts both v1.0 and v2.0 token issuers
- Verifies audience, issuer, and expiry
- Extracts user subject, email, and group claims

**Group-Based Authorization**:
- Azure Entra ID group membership exposed as token claims
- Use `require_group(group_id)` or `require_any_group([group_ids])` dependencies
- Example:
  ```python
  @app.get("/admin-only", dependencies=[Depends(require_group("admin-group-id"))])
  async def admin_endpoint():
      ...
  ```

**Frontend Token Management** ([frontend/src/api/client.ts](frontend/src/api/client.ts)):
- Axios interceptor automatically acquires tokens
- Silent token acquisition with popup fallback
- Tokens automatically added to Authorization header

### Asynchronous Integration

Services communicate via ActiveMQ using the transactional outbox pattern:

1. Application service writes to database + outbox table in single transaction
2. **Outbox Processor** worker polls outbox table
3. Outbox Processor publishes messages to ActiveMQ
4. **Event Consumer** worker subscribes to ActiveMQ topics/queues
5. **Activity Bridge** worker forwards activity events to WebSocket clients

**Key Components**:
- [backend/app/adapters/activemq/publisher.py](backend/app/adapters/activemq/publisher.py) - Message publisher adapter
- [backend/app/entrypoints/workers/outbox_processor.py](backend/app/entrypoints/workers/outbox_processor.py) - Outbox pattern implementation
- [backend/app/entrypoints/workers/consumer.py](backend/app/entrypoints/workers/consumer.py) - Event consumer
- [backend/app/entrypoints/workers/activity_ws_bridge.py](backend/app/entrypoints/workers/activity_ws_bridge.py) - WebSocket bridge

## Data Model

The application models a vinyl record collection with clear separation:
- **Musical works** (Artist, Album, Track)
- **Physical pressings** (Pressing, Matrix/Runout, Packaging)
- **User-owned copies** (Collection Items with condition, purchase info, ratings)
- **Supporting data** (Genres, Styles, Countries, Artist Types, Release Types, Edition Types, Sleeve Types)
- **Integration** (Outbox Events for transactional messaging, External References for Discogs/MusicBrainz links)

**Database Schema**: [infrastructure/postgres/init.sql](infrastructure/postgres/init.sql) contains the complete PostgreSQL schema with triggers and indexes.

See [docs/data-model.md](docs/data-model.md) for complete entity definitions and relationships.

## Adding New Features

Follow hexagonal architecture patterns:

1. **Define Domain Entities** ([backend/app/domain/entities.py](backend/app/domain/entities.py)):
   - Pure Python classes with business rules
   - No framework dependencies

2. **Define Ports** ([backend/app/application/ports/](backend/app/application/ports/)):
   - Create interface contracts (abstract base classes)
   - Example: `RepositoryPort`, `MessagePublisherPort`

3. **Implement Application Service** ([backend/app/application/services/](backend/app/application/services/)):
   - Business orchestration using ports
   - Security-agnostic

4. **Implement Adapters** ([backend/app/adapters/](backend/app/adapters/)):
   - Database repositories (SQLAlchemy)
   - Message publishers (ActiveMQ)

5. **Create HTTP Entrypoint** ([backend/app/entrypoints/http/main.py](backend/app/entrypoints/http/main.py)):
   - FastAPI route
   - Inject `get_current_user` for authentication
   - Add authorization dependencies if needed
   - Call application service

6. **Frontend Integration**:
   - Create UI components ([frontend/src/components/](frontend/src/components/))
   - Use `apiClient` from [frontend/src/api/client.ts](frontend/src/api/client.ts) for authenticated requests
   - Handle loading/error states

## Environment Configuration

Copy [.env.example](.env.example) to `.env` for local development, or [.env.nas](.env.nas) for NAS deployment, and configure:

**Azure Entra ID** (required):
- `AZURE_TENANT_ID` - Your Azure AD tenant ID
- `AZURE_CLIENT_ID` - App registration client ID
- `AZURE_AUDIENCE` - API identifier (format: `api://{client-id}`)
- Configure in Azure Portal → App Registrations:
  - Add SPA platform with redirect URI
  - Expose API scope: `access_as_user`
  - Enable group claims in token configuration

**Database**:
- `POSTGRES_USER`, `POSTGRES_PASSWORD` - PostgreSQL credentials
- `DATABASE_URL` - Connection string

**ActiveMQ**:
- `ACTIVEMQ_URL` - STOMP connection (default: `stomp://activemq:61613`)

**Discogs Service** (optional):
- `DISCOGS_USER_AGENT` - User agent for Discogs API
- `DISCOGS_KEY` - Discogs API consumer key
- `DISCOGS_SECRET` - Discogs API consumer secret
- `DISCOGS_OAUTH_TOKEN` - OAuth access token (optional)
- `DISCOGS_OAUTH_TOKEN_SECRET` - OAuth token secret (optional)
- `DISCOGS_SERVICE_URL` - URL for discogs service (default: `http://discogs-service:8001`)

**Frontend**:
- `VITE_API_URL` - Backend API URL
- `VITE_AZURE_CLIENT_ID`, `VITE_AZURE_TENANT_ID` - Azure config
- `VITE_AZURE_REDIRECT_URI` - Redirect after login

## Service Endpoints (Local Development)

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- ActiveMQ Admin: http://localhost:8161 (admin/admin)
- PostgreSQL: localhost:5432

## Service Endpoints (Synology Deployment)

- Frontend: http://10.254.1.210:3000
- Backend API: http://10.254.1.210:8000
- ActiveMQ Admin: http://10.254.1.210:8161

## Important Architectural Constraints

1. **Security belongs at boundaries only** - Never add authentication/authorization logic to domain or application layers
2. **Respect dependency directions** - Domain is pure, application depends on domain, adapters implement ports
3. **Use ports for all external dependencies** - Database, message queue, external APIs must be accessed via ports
4. **Worker entrypoints are for non-privileged operations** - Don't execute user-specific actions requiring authorization in workers
5. **Frontend authentication is mandatory** - All API calls must include Azure Entra ID bearer tokens
6. **Group-based authorization** - Map Azure AD groups to application roles, check at HTTP entrypoint level

## Database Migrations

**Important**: This project uses a static SQL initialization file rather than migration tools like Alembic.

- Schema is defined in [infrastructure/postgres/init.sql](infrastructure/postgres/init.sql)
- Changes to the schema should be made directly in init.sql
- For production deployments, manual migration scripts may be needed
- Full-text search, triggers, and constraints are defined in init.sql

## Key Reference Documents

- [docs/design-spec.md](docs/design-spec.md) - UI/UX design guidelines, color palette, user types, functional requirements
- [docs/reference-architecture.md](docs/reference-architecture.md) - Complete C4 architecture, authentication flows, authorization patterns
- [docs/data-model.md](docs/data-model.md) - Full entity relationship model for vinyl collection
- [docs/authorization-guide.md](docs/authorization-guide.md) - Detailed guide on implementing authorization
- [README.md](README.md) - Setup instructions, deployment guide, troubleshooting
- [docs/SETUP.md](docs/SETUP.md) - Detailed setup and configuration instructions
- [docs/AZURE-SETUP-CHECKLIST.md](docs/AZURE-SETUP-CHECKLIST.md) - Azure Entra ID configuration checklist
