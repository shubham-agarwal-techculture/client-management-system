"""Alembic environment for the Client Management System."""

import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

from alembic import context

# Import settings and all models so target_metadata is complete.
from app.config import settings  # noqa: E402
import app.models  # noqa: F401  (registers all model modules via main-style imports)
import app.models.client
import app.models.custom_field
import app.models.client_custom_value
import app.models.tag
import app.models.client_tag
import app.models.organization
import app.models.user
import app.models.interaction
import app.models.task
import app.models.document
import app.models.event_log
from app.database import Base  # noqa: E402

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
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    async def run_async() -> None:
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