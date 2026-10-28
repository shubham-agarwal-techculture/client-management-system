"""Alembic environment for the Client Management System."""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context

# Ensure the project root is on sys.path so `app` package is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import settings and all models so target_metadata is complete.
from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402

# Import all model modules to register them on Base.metadata
import app.models.client  # noqa: F401
import app.models.custom_field  # noqa: F401
import app.models.client_custom_value  # noqa: F401
import app.models.tag  # noqa: F401
import app.models.client_tag  # noqa: F401
import app.models.organization  # noqa: F401
import app.models.user  # noqa: F401
import app.models.interaction  # noqa: F401
import app.models.task  # noqa: F401
import app.models.document  # noqa: F401
import app.models.event_log  # noqa: F401

config = context.config
fileConfig(config.config_file_name)

# Override sqlalchemy.url with the value from .env / environment.
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = context.get_context().configure()  # Get the connection

    async def run_async() -> None:
        from sqlalchemy.ext.asyncio import create_async_engine

        connectable = create_async_engine(
            config.get_main_option("sqlalchemy.url"),
            future=True,
        )
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    asyncio.run(run_async())


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()