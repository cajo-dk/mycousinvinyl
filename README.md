# MyCousinVinyl

A full-stack web application built with **React** and **FastAPI** following **Hexagonal Architecture** principles, with **Azure Entra ID** authentication and deployment to **Synology NAS** via Docker.

## Architecture Overview

This project implements a modern, scalable architecture based on the C4 model:

- **Frontend**: React SPA with Azure Entra ID authentication (MSAL)
- **Backend**: Python FastAPI microservices with hexagonal architecture
- **Database**: PostgreSQL with transactional outbox pattern
- **Message Broker**: Apache ActiveMQ (default) or MQTT for asynchronous integration
- **Infrastructure**: Docker containers orchestrated with Docker Compose
- **Deployment**: Synology NAS at 10.254.1.210

### Key Design Principles

1. **Hexagonal Architecture**: Clean separation between domain logic, application use-cases, and infrastructure adapters
2. **Group-Based Authorization**: Azure Entra ID groups mapped to application roles
3. **Security at Boundaries**: Authentication/authorization enforced at API entrypoints, domain remains security-agnostic
4. **Event-Driven Integration**: Services communicate asynchronously via ActiveMQ or MQTT
5. **Containerization**: All components run in isolated Docker containers

## Project Structure

```
mycousinvinyl/
├── frontend/                    # React SPA
│   ├── src/
│   │   ├── app/                # Application components
│   │   ├── auth/               # Azure Entra ID authentication
│   │   ├── api/                # API client with token injection
│   │   ├── components/         # Reusable UI components
│   │   └── features/           # Feature modules
│   ├── Dockerfile
│   └── package.json
│
├── backend/                     # FastAPI microservice
│   ├── app/
│   │   ├── domain/             # Business entities and rules
│   │   ├── application/        # Use-cases and ports
│   │   │   ├── ports/          # Interface contracts
│   │   │   └── services/       # Business orchestration
│   │   ├── adapters/           # Infrastructure implementations
│   │   │   ├── postgres/       # Database adapter
│   │   │   └── activemq/       # Message broker adapter
│   │   └── entrypoints/        # External interfaces
│   │       ├── http/           # REST API with auth
│   │       └── workers/        # Message consumers
│   ├── Dockerfile
│   └── requirements.txt
│
├── infrastructure/
│   ├── postgres/
│   │   └── init.sql            # Database initialization
│   ├── docker/
│   └── activemq/
│
├── docker-compose.yml           # Service orchestration
├── .env.example                 # Environment template
├── deploy-to-synology.ps1       # Windows deployment script
├── deploy-to-synology.sh        # Linux/Mac deployment script
└── reference-architecture.md    # Detailed architecture documentation
```

## Prerequisites

### For Local Development
- Docker Desktop
- Node.js 20+
- Python 3.12+
- Git

### For Synology NAS Deployment
- Synology NAS with Docker support
- SSH access to NAS
- Environment variables: `SYNOLOGY_USER`, `SYNOLOGY_PASSWORD`

### Azure Configuration
- Azure Entra ID tenant
- App Registration with:
  - API permissions: `User.Read`
  - Exposed API scope: `access_as_user`
  - Group claims enabled

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd MyCousinVinyl

# Create environment file
cp .env.example .env
# Edit .env with your Azure credentials and database passwords
```

### 2. Configure Azure Entra ID

1. Go to [Azure Portal](https://portal.azure.com) > Azure Active Directory > App Registrations
2. Create a new app registration
3. Configure authentication:
   - Add platform: Single-page application
   - Redirect URI: `http://localhost:3000`
4. Expose an API:
   - Add scope: `access_as_user`
5. API permissions:
   - Add `User.Read` permission
6. Token configuration:
   - Add groups claim
7. Copy these values to `.env`:
   - `AZURE_TENANT_ID`
   - `AZURE_CLIENT_ID`
   - `AZURE_AUDIENCE` (format: `api://<client-id>`)

### 3. Local Development

#### Run all services locally:

```bash
docker compose up -d
```

#### Run with ActiveMQ health dependency (optional):

```bash
docker compose -f docker-compose.yml -f docker-compose.activemq.yml up -d --build
```

#### Run with MQTT (no ActiveMQ):

```bash
docker compose -f docker-compose.yml -f docker-compose.mqtt.yml up -d --build
```

Tip: set `MQTT_TOPIC_PREFIX` in `.env` to group MQTT topics under a system name (for example: `MyCousinVinyl`).

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ActiveMQ Admin: http://localhost:8161 (admin/admin)
- PostgreSQL: localhost:5432

#### Or run services individually:

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.entrypoints.http.main:app --reload
```

**Worker:**
```bash
cd backend
python -m app.entrypoints.workers.consumer
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 4. Deploy to Synology NAS

#### Windows (PowerShell):
```powershell
# Set environment variables
$env:SYNOLOGY_USER = "your-username"
$env:SYNOLOGY_PASSWORD = "your-password"

# Deploy (with build)
.\deploy-to-synology.ps1 -Build

# Or deploy using pre-built images
.\deploy-to-synology.ps1
```

#### Linux/Mac (Bash):
```bash
# Set environment variables
export SYNOLOGY_USER="your-username"
export SYNOLOGY_PASSWORD="your-password"

# Deploy (with build)
./deploy-to-synology.sh --build

# Or deploy using pre-built images
./deploy-to-synology.sh
```

#### Synology NAS with MQTT (no ActiveMQ):

```bash
docker compose -f docker-compose.nas.yml -f docker-compose.nas.mqtt.yml up -d --build
```

#### Synology NAS with ActiveMQ dependency (optional):

```bash
docker compose -f docker-compose.nas.yml -f docker-compose.nas.activemq.yml up -d --build
```

After deployment, services will be available at:
- Frontend: http://10.254.1.210:3000
- Backend API: http://10.254.1.210:8000
- ActiveMQ Admin: http://10.254.1.210:8161

### 5. Home Assistant Add-on

See `docs/home-assistant-addon.md` for the single-container Home Assistant add-on build and configuration.

## Development Workflow

### Adding a New Feature

1. **Domain Layer** (`backend/app/domain/`):
   - Define entities and business rules
   - Keep security-agnostic

2. **Application Layer** (`backend/app/application/`):
   - Define ports (interfaces)
   - Implement use-case services

3. **Adapters** (`backend/app/adapters/`):
   - Implement repository for database
   - Add message handlers if needed

4. **Entrypoints** (`backend/app/entrypoints/`):
   - Add HTTP endpoints with auth
   - Enforce authorization at this layer
   - Add worker handlers for events

5. **Frontend** (`frontend/src/`):
   - Create UI components
   - Use apiClient for authenticated requests
   - Handle loading and error states

### Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Security Considerations

1. **Authentication**: Enforced via Azure Entra ID at SPA and API boundaries
2. **Authorization**: Group-based, checked at HTTP entrypoints only
3. **Token Validation**: API validates signature, issuer, audience, expiry
4. **CORS**: Configured for specific origins only
5. **Secrets**: Managed via environment variables, never committed to Git

## Monitoring and Logs

### View logs on Synology NAS:
```bash
ssh user@10.254.1.210
cd /volume1/docker/mycousinvinyl
docker compose logs -f [service-name]
```

### View logs locally:
```bash
docker compose logs -f [service-name]
```

Service names: `frontend`, `api`, `worker`, `postgres`, `activemq`

## Troubleshooting

### Authentication Issues
- Verify Azure App Registration configuration
- Check redirect URIs match exactly
- Ensure group claims are enabled
- Verify token audience matches backend config

### Database Connection Issues
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL container is healthy: `docker compose ps`
- Check logs: `docker compose logs postgres`

### Message Queue Issues
- Verify ActiveMQ is running: `docker compose ps`
- Check ActiveMQ admin UI: http://localhost:8161
- Review worker logs: `docker compose logs worker`

### Deployment Issues
- Verify SSH credentials are correct
- Ensure Docker is installed on Synology NAS
- Check NAS firewall rules for required ports
- Verify sufficient disk space on NAS

## Architecture Documentation

For detailed architecture documentation, see:
- [reference-architecture.md](./reference-architecture.md) - Complete C4 architecture documentation

## Contributing

1. Follow the hexagonal architecture patterns
2. Keep security concerns at boundaries
3. Write tests for business logic
4. Update documentation for significant changes

## License

[Your License Here]
