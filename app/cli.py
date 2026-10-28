"""Management CLI: `python -m app.cli <command>`.

Commands:
    seed          Create default organization + admin user + sample clients.
    init-db       Create all tables (dev shortcut; prefer `alembic upgrade head`).
    create-user   Create a user (prompts for email/password/role).
"""

import argparse
import asyncio
import os

from uuid import uuid4

from app.database import Base, create_async_engine, async_sessionmaker
from app.security import get_password_hash
from app.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.models.client import Client


async def seed_demo() -> None:
    """Seed a default organization, admin user, and sample clients."""
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Default organization
    result = await conn.execute(
        select(Organization).where(Organization.slug == "default")
    )
    org = result.scalar_one_or_none()
    if org is None:
        org = Organization(
            name="Default Organization",
            slug="default",
            is_active=True,
        )
        conn.add(org)
        await conn.flush()

    # Admin user
    result = await conn.execute(
        select(User).where(User.email == settings.seed_admin_email)
    )
    if result.scalar_one_or_none() is None:
        session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()
        session.add(
            User(
                email=settings.seed_admin_email,
                hashed_password=get_password_hash(settings.seed_admin_password),
                full_name="Administrator",
                role="admin",
                is_active=True,
                organization_id=org.id,
            )
        )
        await session.commit()
        await session.refresh(session.get(User, settings.seed_admin_email))
        print("Demo data seeded.")
        print(f"  Admin: {settings.seed_admin_email} / {settings.seed_admin_password}")
    else:
        print("Demo data already seeded.")


async def init_db_cmd() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


async def create_user_cmd(email: str, role: str, password: str | None = None) -> None:
    if password is None:
        password = input(f"Password for {email}: ")
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        result = await conn.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            print(f"User {email} already exists.")
            return
        session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()
        session.add(
            User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="",
                role=role,
                is_active=True,
                organization_id=None,
            )
        )
        await session.commit()
        print(f"User {email} created (role={role}).")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli", description="CMS management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed", help="Seed demo data")
    sub.add_parser("init-db", help="Create all tables")

    p_user = sub.add_parser("create-user", help="Create a user")
    p_user.add_argument("--email", required=True)
    p_user.add_argument("--role", default="agent", choices=["admin", "manager", "agent", "viewer"])
    p_user.add_argument("--password", default=None)

    args = parser.parse_args()

    if args.command == "seed":
        asyncio.run(seed_demo())
    elif args.command == "init-db":
        asyncio.run(init_db_cmd())
    elif args.command == "create-user":
        asyncio.run(create_user_cmd(args.email, args.role, args.password))


if __name__ == "__main__":
    main()