# Application Architecture, Development and Design Guide

## Purpose

This guide enables developers and specialists to work with and extend the application.

## 1. Reference Architecture

### Design patterns in use

- Hexagonal architecture (ports/adapters): domain and application logic in `backend/app/domain` and `backend/app/application`; infrastructure in `backend/app/adapters`; entrypoints in `backend/app/entrypoints`.
- Repository + Unit of Work: repository ports in `backend/app/application/ports`, SQLAlchemy adapters in `backend/app/adapters/postgres`, and `SqlAlchemyUnitOfWork`.
- Transactional outbox: `outbox_events` table and `outbox_processor` worker.
- Event-driven integration: broker abstraction with ActiveMQ/MQTT adapters.
- SPA + API: React SPA in `frontend/` with FastAPI HTTP API in `backend/app/entrypoints/http`.

### Rationale behind design choices

- Isolates domain logic from infrastructure to reduce coupling and enable replacement of storage or messaging.
- Port/adapters allow new integrations (message brokers, storage backends) without changes to core logic.
- Outbox guarantees event publication consistency with database changes.
- Workers keep long-running tasks off request paths and reduce API latency.

## 2. Data Model

### Data structures

The schema is defined in `infrastructure/postgres/init.sql`. Core entities are Artist, Album, Track, Pressing, Matrix, Packaging, and CollectionItem. Supporting entities include MediaAsset, ExternalReference, UserPreferences, MarketData, Discogs OAuth, and Discogs cache tables.

```mermaid
classDiagram
    class Artist {
      UUID id
      string name
      string sort_name
      string type
      string country
      int discogs_id
    }
    class Album {
      UUID id
      string title
      UUID primary_artist_id
      int original_release_year
      int discogs_id
    }
    class Track {
      UUID id
      UUID album_id
      string side
      string position
      string title
    }
    class Pressing {
      UUID id
      UUID album_id
      string format
      string speed_rpm
      string size_inches
      int discogs_release_id
      int discogs_master_id
    }
    class Matrix {
      UUID id
      UUID pressing_id
      string side
      string matrix_code
    }
    class Packaging {
      UUID id
      UUID pressing_id
      string sleeve_type
    }
    class CollectionItem {
      UUID id
      UUID user_id
      UUID pressing_id
      string media_condition
      string sleeve_condition
    }
    class MarketData {
      UUID id
      UUID pressing_id
      decimal median_value
      string currency
    }
    class MediaAsset {
      UUID id
      string entity_type
      UUID entity_id
      string media_type
      string url
    }
    class ExternalReference {
      UUID id
      string entity_type
      UUID entity_id
      string source
      string external_id
    }
    class DiscogsUserToken {
      UUID user_id
      string access_token
      string access_secret
      string discogs_username
    }
    class OutboxEvent {
      UUID id
      string event_type
      string destination
      bool processed
    }

    Artist "1" --> "many" Album : primary_artist
    Album "1" --> "many" Track : tracks
    Album "1" --> "many" Pressing : pressings
    Pressing "1" --> "many" Matrix : matrices
    Pressing "1" --> "1" Packaging : packaging
    Pressing "1" --> "many" CollectionItem : owned_by
    Pressing "1" --> "1" MarketData : pricing
    Album "1" --> "many" MediaAsset : media_assets
    Pressing "1" --> "many" ExternalReference : references
```

### How to extend the data model

1. Update `infrastructure/postgres/init.sql` with new tables/columns.
2. Update SQLAlchemy models in `backend/app/adapters/postgres/models.py`.
3. Add or update repository ports in `backend/app/application/ports`.
4. Implement repository adapters in `backend/app/adapters/postgres`.
5. Update services and HTTP schemas in `backend/app/application/services` and `backend/app/entrypoints/http/schemas`.
6. Add tests in `backend/tests`.
7. Run migrations if you use Alembic (included in `backend/requirements.txt`).

## 3. Security Model

### Authentication via Azure Entra

- SPA uses MSAL for login.
- API validates JWT access tokens using Azure JWKS, issuer, and audience.
- User identity uses `oid` (preferred) or `sub` claims.

### RBAC roles

- Admin, Editor, Viewer.
- Group IDs are configured in environment variables and mapped in `backend/app/entrypoints/http/authorization.py`.
- Admin inherits Editor and Viewer access.

### Security implementation

- Authorization enforced at HTTP entrypoints only.
- Domain and application layers are security-agnostic.
- Collection operations are scoped by `user_id` in services.

### CORS implementation

- `CORS_ALLOW_ORIGINS` and `CORS_ALLOW_ORIGIN_REGEX` are configurable via environment variables.
- In non-production, a localhost regex is enabled if no regex is provided.
- Implemented in `backend/app/entrypoints/http/main.py`.

## 4. Service Description

### Services

- Frontend SPA (React + Vite): `frontend/`
- API (FastAPI): `backend/app/entrypoints/http`
- Discogs service: `discogs-service/`
- PostgreSQL
- Message broker: ActiveMQ or MQTT
- Outbox processor
- Event consumer worker
- Pricing worker
- Cache cleanup worker
- Activity bridge worker

### Service relationships (Mermaid UML)

```mermaid
flowchart LR
  UI[Frontend SPA] --> API[FastAPI API]
  API --> DB[(PostgreSQL)]
  API --> DiscogsSvc[Discogs Service]
  DiscogsSvc --> DiscogsAPI[Discogs API]
  API --> Outbox[(outbox_events)]
  OutboxProcessor[Outbox Processor] --> Broker[ActiveMQ or MQTT]
  OutboxProcessor --> Outbox
  Broker --> Worker[Event Consumer]
  Broker --> ActivityBridge[Activity Bridge]
  ActivityBridge --> API
  PricingWorker[Pricing Worker] --> DiscogsSvc
  CacheCleanup[Cache Cleanup] --> DB
  Worker --> DB
```

### Major flows

#### Catalog create/update and event publish

```mermaid
sequenceDiagram
  participant User
  participant SPA as Frontend
  participant API as FastAPI
  participant DB as PostgreSQL
  participant Outbox as outbox_events
  participant Proc as Outbox Processor
  participant Broker as Broker
  participant Worker as Event Consumer

  User->>SPA: Create album/pressing
  SPA->>API: POST /api/v1/albums or /pressings
  API->>DB: Insert record
  API->>Outbox: Insert event
  API-->>SPA: 201 Created
  Proc->>Outbox: Read unprocessed events
  Proc->>Broker: Publish event
  Broker->>Worker: Deliver event
```

#### Discogs lookup

```mermaid
sequenceDiagram
  participant SPA as Frontend
  participant API as FastAPI
  participant DiscogsSvc as Discogs Service
  participant DiscogsAPI as Discogs API

  SPA->>API: /api/v1/discogs/*
  API->>DiscogsSvc: HTTP request
  DiscogsSvc->>DiscogsAPI: /database/search, /artists/{id}, /masters/{id}, /releases/{id}
  DiscogsAPI-->>DiscogsSvc: Response
  DiscogsSvc-->>API: Normalized payload
  API-->>SPA: Response
```

#### Album wizard scan

```mermaid
sequenceDiagram
  participant User
  participant SPA as Frontend
  participant API as FastAPI
  participant Wizard as AlbumWizardClient
  participant DB as PostgreSQL

  User->>SPA: Capture cover
  SPA->>API: POST /api/v1/album-wizard/scan
  API->>Wizard: analyze_cover(image)
  Wizard-->>API: AI result
  API->>DB: Artist/album search
  API-->>SPA: Match result
```

## 5. Discogs Integration

### Authentication

Discogs requests use:

- OAuth 1.0a (token + secret) for user collection features.
- Personal Access Token (PAT) for marketplace pricing.
- Key/secret query params for non-marketplace endpoints.

OAuth and PAT are stored per-user in `discogs_user_tokens`.

### Discogs data model alignment

- Discogs Artist -> `artists`
- Discogs Master -> `albums` (`discogs_id`)
- Discogs Release -> `pressings` (`discogs_release_id`)
- Discogs format/speed/size -> normalized enums

### Discogs API methods used

- `GET /database/search`
- `GET /artists/{id}`
- `GET /masters/{id}`
- `GET /masters/{id}/versions`
- `GET /releases/{id}`
- `GET /marketplace/price_suggestions/{release_id}`

## 6. UX

### General UX guidelines

- Dark theme and high contrast.
- Table-centric browsing for scanning.
- Create/edit via modal dialogs.
- Sticky navigation with quick section access.
- Activity status bar anchored to the bottom on handheld devices.

### Layout

- Top navigation with search and filters.
- Content area constrained to readable width on desktop.
- Mobile layout emphasizes scanning workflows (Album Wizard).

### Colors in use

Foreground:
- Primary text: `#f5f7fa`
- Muted text: `#9a9a9a`

Backgrounds and surfaces:
- App background: `#0b0f14`
- Surface: `#151a1f`
- Surface 2: `#1d232b`
- Border: `rgba(255, 255, 255, 0.08)`
- Accent: `#ff6b35`
- Accent soft: `rgba(255, 107, 53, 0.18)`

### MDI icons in use

- `mdiAlbum`
- `mdiAccountMusicOutline`
- `mdiRecordPlayer`
- `mdiRecordCircleOutline`
- `mdiMusicBoxOutline`
- `mdiMagnify`
- `mdiMagnifyScan`
- `mdiFilterVariant`
- `mdiCamera`
- `mdiCheck`
- `mdiRefresh`
- `mdiPlus`
- `mdiPencilOutline`
- `mdiTrashCanOutline`
- `mdiEyeOutline`
- `mdiInformationBoxOutline`
- `mdiLinkBoxOutline`
- `mdiCog`
- `mdiLogout`
- `mdiMenu`
- `mdiClose`
- `mdiMagicStaff`
- `mdiAccountOutline`
- Dynamic alpha icons: `mdiAlpha{A-Z}`, `mdiAlpha{A-Z}Box`, `mdiAlpha{A-Z}BoxOutline`, `mdiAlpha{A-Z}Circle`, `mdiAlpha{A-Z}CircleOutline`

## 7. Testing

### Unit testing

- Backend unit tests are under `backend/tests/unit`.
- Run with:

```bash
cd backend
pytest
```

### Integration testing

- Integration tests are under `backend/tests/integration`.
- Run with:

```bash
cd backend
pytest tests/integration
```

### Frontend checks

- Linting:

```bash
cd frontend
npm run lint
```
