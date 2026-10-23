"""Pytest configuration and shared fixtures for the CMS test suite."""

import asyncio
from typing import AsyncGenerator, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_session

TEST_DB_URL = "sqlite+aiosqlite:///./test_cms.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    test_engine = create_async_engine(TEST_DB_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    test_engine = create_async_engine(TEST_DB_URL)
    test_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_session_factory() as s:
        yield s
    await test_engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def make_user(session: AsyncSession) -> Callable:
    from app.models.user import User
    from app.models.organization import Organization
    from app.security import get_password_hash

    async def _make(email="user@example.com", role="agent", password="password123"):
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            return result.scalar_one()
        org_result = await session.execute(
            select(Organization).where(Organization.slug == "test-org")
        )
        org = org_result.scalar_one_or_none()
        if org is None:
            org = Organization(name="Test Org", slug="test-org", is_active=True)
            session.add(org)
            await session.flush()
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Test User",
            role=role,
            is_active=True,
            organization_id=org.id,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    return _make


@pytest.fixture
async def auth_headers(client: AsyncClient, make_user) -> Callable:
    async def _headers(email="user@example.com", password="password123", role="agent"):
        await make_user(email=email, role=role, password=password)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200, resp.text
        tokens = resp.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}

    return _headers