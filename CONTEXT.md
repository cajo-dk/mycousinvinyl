# AI Coding Assistant - Project Context & Guardrails

> Purpose:
> This document provides authoritative context for AI coding assistants and human contributors.
> It defines intent, constraints, standards, and open questions to ensure consistent, maintainable, and predictable outcomes.

---

## 1. Problem Statement & Desired Outcomes

### Problem Statement

- MyCousinVinyl helps collectors manage a personal vinyl library with rich metadata, condition tracking, and value insights.
- The primary users are individual collectors who want a private, fast-to-navigate catalog that does not depend on public collection exposure.
- This matters now because collections grow and Discogs-style data is useful but cumbersome to manage across spreadsheets and scattered notes.
- Current solutions make scanning, filtering, and maintaining consistent pressing-level details too slow or too manual.

### Desired Outcomes

- Users can quickly create, edit, and browse artists, albums, pressings, and their owned collection items.
- The collection remains private per user; no cross-user data exposure.
- Discogs integration accelerates data entry and provides market data.
- Success is defined by: fast table-based browsing, reliable CRUD workflows, and correct scoping by `user_id`.
- Out of scope: public marketplace features, cross-user sharing, and native mobile apps.

---

## 2. Scope

### In Scope

- Personal collection management for Artists, Albums, Pressings, and Collection Items.
- Table-based browsing with search, filters, and modal create/edit flows.
- Discogs lookup and pricing integration via the Discogs service.
- Role-based access control (Admin > Editor > Viewer) via Azure Entra ID groups.
- Async event publishing using a transactional outbox and message broker.
- Limited cross-user visibility for small groups (families) of up to 4 people, where group members ownership of a pressing is indicated by the member's chosen icon on various listings for all group mmbers to see.

### Out of Scope

- Full cross-user visibility or administrative access to other users' collections.
- Marketplace features (buy/sell, price negotiation, trading).
- Native mobile clients; the UI is a responsive SPA (PWA-capable).

### Constraints

- Authorization is enforced only at HTTP entrypoints; domain/application layers remain security-agnostic.
- Collection operations must be scoped by `user_id`.
- Docker-first deployment with Postgres and ActiveMQ/MQTT.
- Dark theme with MDI icons, tables for scanning, and modals for create/edit flows.

---

## 3. System Context & Architecture

### System Context

- Users authenticate with Azure Entra ID and interact with the SPA in a browser.
- The SPA calls FastAPI HTTP endpoints with bearer tokens.
- The API integrates with a Discogs proxy service and publishes events via an outbox and broker.
- Workers consume trusted internal events only (no user auth context).

### Architecture

- SPA + API + workers, with hexagonal backend architecture.
- Backend layers: domain (`backend/app/domain`), application (`backend/app/application`), ports, adapters, entrypoints.
- Communication:
  - Sync: HTTP/JSON between SPA and API, API and Discogs service.
  - Async: outbox -> broker (ActiveMQ/MQTT) -> workers.
- Patterns:
  - Repository + Unit of Work
  - Transactional outbox
  - Ports/adapters isolation
- Avoid: authorization logic inside domain/application layers.

---

## 4. UX Principles & Style Rules

### UX Principles

- Primary users are collectors who need fast scanning of large lists.
- Prioritize speed, clarity, and low-friction CRUD workflows.
- Core workflows: browse tables, search/filter, open modals to create/edit, and track collection stats.

### Style Rules

- Dark theme with high contrast and warm accent.
- Typography:
  - Primary font: `Space Grotesk`
  - Mono font: `JetBrains Mono`
- Colors (from `frontend/src/app/index.css`):
  - App background: `#0b0f14` (with radial gradients)
  - Surface: `#151a1f`
  - Surface 2: `#1d232b`
  - Border: `rgba(255, 255, 255, 0.08)`
  - Accent: `#ff6b35`
  - Accent soft: `rgba(255, 107, 53, 0.18)`
  - Primary text: `#f5f7fa`
- Theme token aliases used in components (should be defined in `:root` to avoid undefined vars):
  - `--surface-color` -> `--app-surface`
  - `--border-color` -> `--app-border`
  - `--primary-color` -> `--app-accent`
  - `--primary-rgb` -> `255, 107, 53` (RGB for `#ff6b35`)
  - `--text-secondary` -> `--color-text-muted` (secondary text)
  - `--primary-light` / `--primary-hover` -> lighter variants of `--app-accent`
  - `--color-text` -> `#f5f7fa`
  - `--color-text-muted` -> `#999`
  - `--color-border` -> `#333` or `--app-border` (align to theme tokens)
  - `--color-border-strong` -> `#444`
  - `--color-background-subtle` -> `#1a1a1a` (common surface tone)
  - `--color-background-hover` -> `#222`
  - `--color-background-selected` -> `#2a2a2a`
- Icons: Material Design Icons (mdi). Common icons include album, artist, pressing, search, filter, add, edit, delete, info.
- Layout:
  - Sticky top navigation with global search.
  - Content max width on desktop; responsive stacking on mobile.
  - Bottom activity status bar for async updates.
- Accessibility:
  - Visible focus states and adequate text contrast.
  - Modals close via Escape; table actions should be keyboard reachable.

---

## 5. Technology Stack

### Frontend

- React 18 + Vite, served by nginx.
- Routing: `react-router-dom`.
- Auth: MSAL (`@azure/msal-browser`, `@azure/msal-react`).
- API client: Axios.
- Icons: `@mdi/js`.

### Backend

- Python 3.12, FastAPI, Pydantic v2.
- Hexagonal architecture with ports/adapters.
- SQLAlchemy for persistence.

### Infrastructure & Platform

- PostgreSQL (service-owned schema).
- Message broker: ActiveMQ (default) or MQTT.
- Discogs proxy service for external API calls.
- Docker Compose for local and NAS deployments.

### Versioning

- Python 3.12 (CI and local tooling).
- Node.js 20+ for frontend tooling.
- Frontend uses Vite build modes (`build`, `build:nas`).

---

## 6. Domain Model & Terminology

### Domain Concepts

- Artist: a musical artist or group.
- Album: a release concept; can have multiple pressings.
- Track: a track on an album (side/position).
- Pressing: a physical release variant (format, size, speed).
- Matrix: runout/matrix codes per pressing side.
- Packaging: packaging details for a pressing.
- CollectionItem: a user-owned copy of a pressing; scoped by `user_id`.
- MarketData: optional market valuation for a pressing.
- MediaAsset: images/videos linked to entities.
- ExternalReference: links to Discogs and other sources.
- UserPreferences: per-user settings.

### Terminology

- Album vs Pressing: albums are abstract releases; pressings are physical variants.
- CollectionItem: always user-scoped ownership; never shared across users.
- Discogs Master maps to Album; Discogs Release maps to Pressing.
- Use domain terms in APIs, UI labels, and code naming.

---

## 7. Coding Standards

### General Principles

- Favor clarity and small, focused changes.
- Keep hexagonal boundaries: domain and application layers remain infra-agnostic.
- Keep authorization at HTTP entrypoints; do not leak auth into domain logic.
- Always scope collection operations by `user_id`.

### Language-Specific Rules

- Python: 120-char line limit (`.pylintrc`), Pylint CI check (errors only).
- Frontend: ESLint (`npm run lint`) and TypeScript.
- Use Pydantic models for request/response validation.

### Anti-Patterns

- Adding authorization logic inside domain/application services.
- Skipping `user_id` scoping on collection reads or writes.
- Bypassing outbox when publishing integration events.
- Introducing new frameworks or design systems without explicit approval.

---

## 8. Data Contracts

### Internal Contracts

- API contracts are defined with FastAPI + Pydantic; OpenAPI is available at `/docs`.
- JSON over HTTP is the primary serialization format.
- Outbox events store `event_type`, `event_version`, `aggregate_id`, `destination`, and JSON payloads.

### External Contracts

- Azure Entra ID tokens (JWT) for authentication.
- Discogs API via the Discogs service (search, artist, master, release, pricing).
- Message broker payloads are JSON from the outbox schema.

---

## 9. Security Requirements

### Authentication & Authorization

- Azure Entra ID is the identity provider.
- Group-based RBAC: Admin > Editor > Viewer (Admin inherits Editor).
- Authorization is enforced only at HTTP entrypoints.
- Workers process trusted internal events only.
- RBAC matrix (current HTTP entrypoints):
  - Viewer:
    - Read catalog: artists, albums, pressings, tracks.
    - Read own collection, stats, and import status.
    - Discogs OAuth/PAT connect, status, and disconnect.
    - Album Wizard scan.
    - Collection sharing (settings, follows, owners, search).
    - Lookup reads (genres, styles, countries, types).
  - Editor:
    - All Viewer permissions.
    - Create/update/delete artists, albums, pressings, tracks.
    - Add/update/remove collection items and update condition/purchase/rating/play counts.
    - Discogs metadata search/lookups (artist/album/master/release endpoints).
    - Discogs collection imports and sync.
    - Lookup write endpoints for genres, styles, and countries.
  - Admin:
    - All Editor permissions.
    - Lookup write endpoints for artist types, release types, edition types, sleeve types.
    - System logs and log retention settings.
    - Admin tools (backup).
  - RBAC strictness:
    - If no group IDs are configured and `rbac_strict` is false (or non-production), all authenticated users are allowed.

### Data Protection

- Secrets and credentials are provided via environment variables.
- Use TLS in deployment (handled by reverse proxy/ingress, not in-app).

### Threat Considerations

- Avoid cross-user data leakage; enforce `user_id` scoping.
- Validate JWT issuer, audience, and signature.
- Treat broker events as internal-only and never as user input.

---

## 10. Feature Requests & User Stories

### Feature Definition

- Define the user problem, target role, and expected workflow impact.
- Confirm how it affects tables, modal flows, and RBAC.

### User Story Template

> As a [role]
> I want [capability]
> So that [outcome]

### Acceptance Criteria

- Explicit success conditions and failure handling.
- Edge cases for user-scoped data.
- UI/UX behavior in tables and modal dialogs.

---

## 11. Test Strategies

### Test Types

- Unit tests: backend services, domain logic, and adapters (`backend/tests/unit`).
- Integration tests: API + DB boundaries (`backend/tests/integration`).

### Quality Gates

- Backend: `pytest` and Pylint in CI.
- Frontend: `npm run lint`.
- Health checks: `GET /health` for API and Discogs service.

---

## 12. Non-Functional Requirements

### Performance

- Keep API requests responsive by offloading long-running work to workers.
- Tables and search should remain usable with large collections.

### Reliability

- Use the transactional outbox for reliable event publishing.
- Provide health endpoints for liveness checks.

### Maintainability

- Preserve hexagonal boundaries and clear module ownership.
- Update schema in `infrastructure/postgres/init.sql` and add migrations as needed.

---

## 13. Repository Conventions

### Structure

- Backend: `backend/app` (domain, application, ports, adapters, entrypoints).
- Frontend: `frontend/src` (pages, components, api).
- Infra: `infrastructure/postgres/init.sql`.

### Workflow

- Keep PRs focused; avoid unrelated refactors.
- Use Trunk Based Development practices:
  - Changes should only be committed to the main branch via a pull request.
  - A Feature Request (FR) should always be coded and tested within its own branch. When asked to start working on a feature, you must create a new branch named after the feature request. For FR-001, you must create a branch named fr-001 and implement the feature request within that branch.
  - When instructed to merge the feature, you must create a Pull Request (PR) and merge the branch into main.
  - When not actively working on a FR, you are in Fix Mode, and all changes should be made on a fix branch, e.g., fix-0001. You may open fix branches as necessary and merge them when instructed to do so.

### Tooling

- Docker Compose for local/NAS deployment.
- ESLint for frontend, Pylint/pytest for backend.

---

## 14. Known Trade-Offs & Open Questions

### Explicit Trade-Offs

- Authorization at entrypoints only favors simplicity but requires strict entrypoint discipline.
- Table-heavy UI optimizes scanning over richer card layouts.
- Service-owned schema keeps boundaries clear but limits cross-service queries.

### Open Questions

- None currently.

---

## Instructions to AI Coding Assistants

- Follow this document as source of truth.
- Ask for clarification if requirements conflict or are ambiguous.
- Prefer consistency and maintainability over novelty.
- Do not introduce new technologies or patterns without explicit approval.

## Document Change Log

| Revision | Date (YYYY-MM-DD) | Notes         |
| -------- | ----------------- | ------------- |
| 1.0.0    | 2026-01-16        | First version |
