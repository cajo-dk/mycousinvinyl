# Database Migrations (Alembic)

## Overview

The backend runs `alembic upgrade head` on API startup. If migrations fail, the API will not start.

If the database already has tables created by `infrastructure/postgres/init.sql` but does not yet
have an `alembic_version` table, the backend will automatically stamp the database to `head` and
then continue with normal Alembic upgrades.

## Creating a Migration

1. Ensure `DATABASE_URL` points to the target database.
2. Generate a migration:
   - `alembic revision --autogenerate -m "short description"`
3. Review the generated file under `backend/alembic/versions/`:
   - Verify enum/type changes are explicit and safe.
   - Avoid destructive changes without a clear rollback plan.

## Applying Migrations Manually

- `alembic upgrade head`
- To mark an existing schema as up-to-date without running migrations:
  - `alembic stamp head`

## Enum/Type Conventions

- Create new types explicitly in migrations.
- Avoid dropping types that are still referenced.
- For type changes, add new type values or create a replacement type with data migration steps.
