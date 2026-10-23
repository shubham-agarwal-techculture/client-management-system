"""Management CLI: `python -m app.cli <command>`.

Commands:
    seed          Create default organization + admin user + sample clients.
    init-db       Create all tables (dev shortcut; prefer `alembic upgrade head`).
    create-user   Create a user (prompts for email/password/role).
"""

import argparse
import asyncio
import getpass
from uuid import uuid4

from sqlalchemy import select

from app.database import async_session_factory, init_db
from app.security import get_password_hash
from app.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.models.client import Client
from app.models.custom_field import CustomField
from app.models.tag import Tag
from app.models.client_tag import ClientTag


async def seed_demo() -> None:
    """Seed a default organization, admin user, and sample clients."""
    async with async_session_factory() as session:
        # Default organization
        result = await session.execute(
            select(Organization).where(Organization.slug == "default")
        )
        org = result.scalar_one_or_none()
        if org is None:
            org = Organization(
                name="Default Organization",
                slug="default",
                is_active=True,
            )
            session.add(org)
            await session.flush()

        # Admin user
        result = await session.execute(
            select(User).where(User.email == settings.seed_admin_email)
        )
        if result.scalar_one_or_none() is None:
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
            await session.flush()

        # Sample custom fields + clients (domain-neutral examples)
        cf_lead_source = CustomField(
            organization_id=org.id,
            name="Lead Source",
            field_type="select",
            options='["website","referral","cold-call","partner"]',
            required=False,
            is_active=True,
        )
        cf_budget = CustomField(
            organization_id=org.id,
            name="Budget",
            field_type="number",
            required=False,
            is_active=True,
        )
        session.add_all([cf_lead_source, cf_budget])
        await session.flush()

        sample = Client(
            organization_id=org.id,
            name="Acme Corporation",
            client_type="prospect",
            status="active",
            email="contact@acme.example",
            phone="+1-555-0100",
            notes="Sample client for demonstration.",
        )
        session.add(sample)
        await session.flush()
        # create a tag properly
        tag = Tag(name="hot-lead", organization_id=org.id)
        session.add(tag)
        await session.flush()
        session.add(ClientTag(client_id=sample.id, tag_id=tag.id))

        await session.commit()
        print("Demo data seeded.")
        print(f"  Admin: {settings.seed_admin_email} / {settings.seed_admin_password}")


async def init_db_cmd() -> None:
    await init_db()
    print("Tables created.")


async def create_user_cmd(email: str, role: str, password: str | None = None) -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"User {email} already exists.")
            return
        if password is None:
            password = getpass.getpass(f"Password for {email}: ")
        session.add(
            User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="",
                role=role,
                is_active=True,
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