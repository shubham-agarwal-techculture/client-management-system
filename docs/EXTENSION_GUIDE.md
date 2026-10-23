# Extension Guide

The system is designed so that domain-specific behaviour is added **without
modifying core code**.

## 1. Add a custom client attribute (no code)

Use `POST /api/v1/custom-fields` to define a field (e.g. "Property Type",
"Candidate Tier", "Contract Value"), then send it with client create/update
requests via the `custom_values` list:

```json
{
  "name": "Acme Corp",
  "custom_values": [
    {"field_id": "<uuid>", "value": "Enterprise"}
  ],
  "tag_names": ["vip", "real-estate"]
}
```

Read them back via `GET /api/v1/clients/{id}` in the `custom_values` map.

## 2. React to lifecycle events

Register handlers on the global event bus (`app.core.hooks.event_bus`):

```python
from app.core.hooks import event_bus, CLIENT_AFTER_CREATE

@event_bus.on(CLIENT_AFTER_CREATE)
async def notify_team(client, actor):
    # e.g. send Slack/email, create a follow-up task, enrich a CRM record
    print(f"New client {client.name} created by {actor}")
```

Standard events: `client.before_create/after_create`,
`client.before_update/after_update`, `client.before_delete/after_delete`,
`interaction.after_create`, `task.after_create`,
`task.after_status_change`, `document.after_upload`.

## 3. Add a new storage backend

Subclass `app.services.storage.StorageBackend`, implement `save`/`get_url`/
`delete`, then wire it:

```python
# app/config.py (or a startup override)
from app.services.storage import StorageBackend
# return your backend from get_storage_backend() based on settings
```

Default: local filesystem. S3-compatible implementation included (requires
`boto3`).

## 4. Add a new API resource

1. Add a SQLAlchemy model in `app/models/` (extend `UUIDMixin`,
   `TimestampMixin`).
2. Add Pydantic schemas in `app/schemas/`.
3. Add a service in `app/services/` following `ClientService` patterns
   (session + actor constructor, event emissions, audit logging).
4. Add a router in `app/api/v1/` and register it in `app/main.py`.
5. Create an Alembic migration: `alembic revision --autogenerate`.

## 5. Change auth / multi-tenancy

- Swap the JWT backend in `app/security.py` or add an API-key dependency.
- Toggle `MULTI_TENANT=false` in `.env` for single-tenant mode (organization
  checks become optional).
- Add role checks with `require_roles("admin", "manager")` dependencies.

## 6. Import from legacy systems

Use `POST /api/v1/import-export/import/clients` (JSON) or the CSV export to
migrate data. Custom fields and tags are created on-the-fly during import.
