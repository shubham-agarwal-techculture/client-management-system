# Architecture

## Overview

The Client Management System is a layered, domain-agnostic application:

```
HTTP layer (FastAPI routers)
    ↓
API layer (request validation via Pydantic schemas)
    ↓
Service layer (business logic, hooks, audit logging)
    ↓
Data layer (SQLAlchemy async models + Alembic migrations)
    ↓
Pluggable backends (document storage, auth providers, event handlers)
```

## Layers

### 1. HTTP/API layer (`app/api/v1/`)
REST resources built with FastAPI. Every endpoint returns consistent JSON;
list endpoints return paginated envelopes. OpenAPI docs are generated
automatically at `/docs`.

### 2. Service layer (`app/services/`)
Thin services encapsulate business rules. Each service receives an async SQLAlchemy
session and the current actor (`User`). Services emit domain events via the event
bus and write audit records to `event_logs`.

### 3. Data layer (`app/models/`)
SQLAlchemy 2.0 declarative models. Shared mixins:
- `UUIDMixin` — UUID primary keys
- `TimestampMixin` — created_at/updated_at
- `SoftDeleteMixin` — soft deletes (clients, users)

### 4. Pluggable backends
- **Storage** (`app/services/storage.py`): `StorageBackend` ABC with `local`
  (filesystem, default) and `s3` (S3-compatible via boto3) implementations.
- **Events** (`app/core/hooks.py`): `EventBus` pub/sub; register handlers with
  `@event_bus.on("client.after_create")`.
- **Database**: async SQLAlchemy; SQLite by default, swap the `DATABASE_URL`
  for PostgreSQL/MySQL.

## Domain-agnostic design

Nothing is hard-coded to an industry:
- Clients carry `client_type`/`status` as free-form strings.
- **Custom fields** (`custom_fields` / `client_custom_values`) let admins define
  arbitrary attributes (text, number, date, boolean, select) via the API — zero
  schema migrations per new field.
- **Tags** provide cross-cutting classification.
- **Interactions** use an open-ended `interaction_type` (call, email, meeting,
  note, visit, other).

## Multi-tenancy & security

- `organizations` are the tenancy boundary; clients, users, tags, custom fields
  and documents reference an organization.
- JWT access + refresh tokens; bcrypt password hashing.
- RBAC roles: `admin`, `manager`, `agent`, `viewer` (enforced via FastAPI
  dependencies `RequireAdmin` / `RequireManager` / `RequireAgent`).

## Extensibility points

See `docs/EXTENSION_GUIDE.md`.
