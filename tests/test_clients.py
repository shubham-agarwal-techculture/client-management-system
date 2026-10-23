"""Client CRUD, custom fields, tags, filtering, soft-delete tests."""

import pytest


@pytest.mark.anyio
async def test_create_and_get_client(client, auth_headers):
    await auth_headers(role="agent")
    resp = await client.post(
        "/api/v1/clients",
        json={
            "name": "Globex Corp",
            "client_type": "prospect",
            "status": "active",
            "email": "contact@globex.example",
            "phone": "+1-555-0100",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Globex Corp"
    assert data["status"] == "active"
    client_id = data["id"]

    resp = await client.get(f"/api/v1/clients/{client_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Globex Corp"


@pytest.mark.anyio
async def test_list_clients_pagination_and_filters(client, auth_headers):
    await auth_headers(role="agent")
    for i in range(5):
        await client.post(
            "/api/v1/clients",
            json={"name": f"Client {i}", "status": "active" if i % 2 == 0 else "inactive"},
        )
    resp = await client.get("/api/v1/clients?page=1&page_size=3")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["page"] == 1
    assert body["page_size"] == 3
    assert body["total_pages"] == 2
    assert body["has_next"] is True
    assert len(body["items"]) == 3

    resp = await client.get("/api/v1/clients?status=inactive")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    resp = await client.get("/api/v1/clients?search=Client 1")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.anyio
async def test_update_client(client, auth_headers):
    await auth_headers(role="agent")
    create = await client.post(
        "/api/v1/clients",
        json={"name": "Old Name", "status": "active"},
    )
    cid = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/clients/{cid}",
        json={"name": "New Name", "status": "inactive"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["status"] == "inactive"


@pytest.mark.anyio
async def test_delete_client_soft(client, auth_headers):
    await auth_headers(role="manager")
    create = await client.post(
        "/api/v1/clients",
        json={"name": "To Delete", "status": "active"},
    )
    cid = create.json()["id"]

    resp = await client.delete(f"/api/v1/clients/{cid}")
    assert resp.status_code == 204

    # excluded from normal list
    resp = await client.get("/api/v1/clients")
    ids = [i["id"] for i in resp.json()["items"]]
    assert cid not in ids

    # included in archived list
    resp = await client.get("/api/v1/clients?archived=true")
    ids = [i["id"] for i in resp.json()["items"]]
    assert cid in ids


@pytest.mark.anyio
async def test_client_custom_values_and_tags(client, auth_headers):
    await auth_headers(role="manager")

    # define a custom field
    cf = await client.post(
        "/api/v1/custom-fields",
        json={
            "name": "Lead Source",
            "field_type": "select",
            "options": ["web", "referral"],
            "required": False,
        },
    )
    assert cf.status_code == 201, cf.text
    field_id = cf.json()["id"]

    create = await client.post(
        "/api/v1/clients",
        json={
            "name": "Lead Client",
            "custom_values": [{"field_id": field_id, "value": "web"}],
            "tag_names": ["hot", "web-lead"],
        },
    )
    assert create.status_code == 201, create.text
    data = create.json()
    assert data["custom_values"] == {"Lead Source": "web"}
    assert set(data["tag_names"]) == {"hot", "web-lead"}

    # filter by tag
    resp = await client.get("/api/v1/clients?tag=hot")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1