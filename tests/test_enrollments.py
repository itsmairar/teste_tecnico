import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_create_enrollment_success(
    mongo_test_db, redis_mock, token_header
):
    payload = {"name": "João", "cpf": "12345678900", "age": 10}
    await mongo_test_db["age_groups"].insert_one({"min_age": 5, "max_age": 15})
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/enrollments/", json=payload, headers=token_header
        )
    assert response.status_code == 202
    assert response.json()["cpf"] == payload["cpf"]
    redis_mock().rpush.assert_called_once()


@pytest.mark.asyncio
async def test_create_enrollment_existing_cpf(mongo_test_db, token_header):
    await mongo_test_db["enrollments"].insert_one(
        {"name": "Maria", "cpf": "12345678900", "age": 10}
    )
    payload = {"name": "Outro", "cpf": "12345678900", "age": 10}
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/enrollments/", json=payload, headers=token_header
        )
    assert response.status_code == 400
    assert "Já existe uma matrícula" in response.text


@pytest.mark.asyncio
async def test_create_enrollment_age_not_matched(mongo_test_db, token_header):
    payload = {"name": "Sem Grupo", "cpf": "11122233344", "age": 99}
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/enrollments/", json=payload, headers=token_header
        )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_list_enrollments_empty(mongo_test_db, token_header):
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/enrollments/", headers=token_header
        )
    assert response.status_code == 200
    assert response.json() == []
