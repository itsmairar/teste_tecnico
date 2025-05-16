import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_create_age_group_success(mongo_test_db, token_header):
    payload = {"min_age": 20, "max_age": 29}
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/age-groups/", json=payload, headers=token_header
        )
    assert response.status_code == 201
    assert response.json()["min_age"] == 20


@pytest.mark.asyncio
async def test_create_age_group_invalid_range(token_header):
    payload = {"min_age": 30, "max_age": 20}
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/age-groups/", json=payload, headers=token_header
        )
    assert response.status_code == 400
    assert "min_age deve ser menor que max_age" in response.text


@pytest.mark.asyncio
async def test_create_age_group_overlap(mongo_test_db, token_header):
    await mongo_test_db["age_groups"].insert_one(
        {"min_age": 10, "max_age": 20}
    )
    payload = {"min_age": 15, "max_age": 25}
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/age-groups/", json=payload, headers=token_header
        )
    assert response.status_code == 400
    assert "sobreposta" in response.text


@pytest.mark.asyncio
async def test_list_age_groups(mongo_test_db, token_header):
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/age-groups/", headers=token_header
        )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_age_group(mongo_test_db, token_header):
    doc = await mongo_test_db["age_groups"].insert_one(
        {"min_age": 70, "max_age": 80}
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/api/v1/age-groups/{str(doc.inserted_id)}", headers=token_header
        )
    assert response.status_code == 200
    assert "removido com sucesso" in response.text
