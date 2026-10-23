"""Authentication tests."""

import pytest


@pytest.mark.anyio
async def test_login_success(client, auth_headers):
    headers = await auth_headers(email="alice@example.com", password="secret123")
    assert "Authorization" in headers


@pytest.mark.anyio
async def test_login_wrong_password(client, make_user):
    await make_user(email="bob@example.com", password="secret123")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_unknown_user(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nope@example.com", "password": "x"},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_me(client, auth_headers):
    await auth_headers(email="carol@example.com", password="secret123")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "secret123"},
    )
    token = resp.json()["access_token"]
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "carol@example.com"


@pytest.mark.anyio
async def test_create_user_requires_admin(client, auth_headers, make_user):
    # agent cannot create users
    await auth_headers(email="agent@example.com", role="agent")
    resp = await client.post(
        "/api/v1/auth/users",
        json={
            "email": "new@example.com",
            "password": "pw123456",
            "role": "agent",
        },
    )
    assert resp.status_code == 403

    # admin can
    await auth_headers(email="admin@example.com", role="admin")
    resp = await client.post(
        "/api/v1/auth/users",
        json={
            "email": "new@example.com",
            "password": "pw123456",
            "role": "agent",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"