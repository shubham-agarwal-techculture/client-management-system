# Client Management System (CMS)

A **generally adaptable, domain-agnostic client management system** with all the basic
requirements of such a system, designed to be extended and used in *any* domain
(real estate, recruiting, consulting, SaaS, non-profit, legal, healthcare, …).

## Core philosophy

- **Client is the central entity**, but nothing about it is hard-coded to a vertical.
- **Extensible without forking:** custom fields, tags, interaction types, document storage,
  and an event hook system let you add domain-specific behaviour via configuration or
  small plug-in modules.
- **API-first:** a full FastAPI REST API with auto-generated OpenAPI docs. A lightweight
  HTMX admin UI is included for immediate out-of-the-box use.
- **Multi-tenant ready:** Organizations + Users with RBAC; runs equally well in
  single-tenant mode.
- **Zero-lock-in storage:** SQLite by default (no setup), swap to PostgreSQL/MySQL by
  changing one environment variable.

## Features

| Area | Capabilities |
|------|--------------|
| Clients | CRUD, status/type classification, owner assignment, search, filtering, pagination |
| Custom fields | Define arbitrary fields (text/number/date/select/boolean) per client via the API/UI |
| Tags | Many-to-many tagging for cross-domain classification |
| Interactions | Log calls, emails, meetings, notes, or custom types against any client |
| Tasks | Client-linked or standalone to-dos with priority, due date, assignee, status |
| Documents | Attach files; pluggable storage (local disk default, S3-compatible swap) |
| Auth & RBAC | JWT auth, roles (admin/manager/agent/viewer), per-endpoint permissions |
| Multi-tenancy | Organizations isolate data; users belong to organizations |
| Events / hooks | `before_*` / `after_*` hooks on client, interaction, task, document lifecycle |
| Import / export | CSV and JSON import/export for clients |
| UI | HTMX server-rendered admin (no build step) + Swagger/OpenAPI docs |
| DevOps | Alembic migrations, Docker, pytest suite, CLI management commands |

## Quick start

```bash
# 1. Create a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# edit .env as needed (defaults work with SQLite)

# 4. Run migrations
alembic upgrade head

# 5. Seed demo data (optional)
python -m app.cli seed

# 6. Start the server
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the API, or `http://localhost:8000/ui/` for the admin UI.

Default seed account: `admin@example.com` / `admin123` (change in production).

## Project layout

```
client-management-system/
├── app/                 # Application source
│   ├── main.py          # FastAPI app factory
│   ├── config.py        # Pydantic settings
│   ├── database.py      # Async SQLAlchemy engine/session
│   ├── security.py      # JWT / password hashing
│   ├── dependencies.py  # FastAPI dependencies (auth, pagination)
│   ├── cli.py           # Management CLI (seed, shell, etc.)
│   ├── api/             # REST API routers (v1)
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic + storage abstraction + event bus
│   ├── core/            # Hooks, exceptions, pagination
│   └── ui/              # HTMX admin templates & routes
├── alembic/             # Database migrations
├── tests/               # pytest suite
├── docs/                # ARCHITECTURE.md, EXTENSION_GUIDE.md
├── pyproject.toml
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Extending the system (high level)

See `docs/EXTENSION_GUIDE.md` for the full guide. The most common extension points:

1. **New client attribute** → create a `CustomField` via the API (no code change).
2. **Domain logic on save** → register a handler on `app.core.hooks.event_bus` for
   `client.after_create`, `client.before_update`, etc.
3. **New storage backend** → subclass `app.services.storage.StorageBackend`
   (`save`, `get_url`, `delete`) and bind it in `config.py`.
4. **New API resource** → add a router under `app/api/v1/` following the existing
   pattern and register it in `app/main.py`.
5. **New interaction type** → just use a new `interaction_type` string; no migration needed.

## License

MIT. See `LICENSE` if you add one.
