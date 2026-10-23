"""Custom field definition tests."""

import pytest


@pytest.mark.anyio
async def test_custom_field_crud(client, auth_headers):
    await auth_headers(role="manager")

    resp = await client.post(
        "/api/v1/custom-fields",
        json={
            "name": "Budget",
            "field_type": "number",
            "required": True,
        },
    )
    assert resp.status_code == 201, resp.text
    fid = resp.json()["id"]

    resp = await client.get("/api/v1/custom-fields")
    assert resp.status_code == 200
    assert any(f["id"] == fid for f in resp.json())

    resp = await client.patch(
        f"/api/v1/custom-fields/{fid}",
        json={"name": "Annual Budget", "is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Annual Budget"
    assert resp.json()["is_active"] is False

    resp = await client.delete(f"/api/v1/custom-fields/{fid}")
    assert resp.status_code == 204

    resp = await client.get("/api/v1/custom-fields")
    assert all(f["id"] != fid for f in resp.json())