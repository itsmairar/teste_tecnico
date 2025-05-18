"""
Testes para endpoints de Matrículas
"""

import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import asyncio  # noqa: E402
import base64  # noqa: E402

import pytest  # noqa: E402
from bson import ObjectId  # noqa: E402
from fastapi import status  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.core.database as database  # noqa: E402
import app.services.age_group_service as ag_service  # noqa: E402
import app.services.enrollment_service as enr_service  # noqa: E402
from app.core.configs import settings  # noqa: E402
from app.services.redis_producer import RedisProducer  # noqa: E402
from main import app  # noqa: E402


# Dummy Collection com suporte async for
class DummyCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs.append(doc)

        class Res:
            inserted_id = doc["_id"]

        return Res()

    async def find_one(self, filter):
        for d in self.docs:
            match = True
            for k, v in filter.items():
                if isinstance(v, dict):
                    if "$lte" in v and not (d.get(k) <= v["$lte"]):
                        match = False
                    if "$gte" in v and not (d.get(k) >= v["$gte"]):
                        match = False
                else:
                    if d.get(k) != v:
                        match = False
            if match:
                return d
        return None

    def find(self, filter):
        class Cursor:
            def __init__(self, docs):
                self._iter = iter(docs)

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration

        return Cursor(self.docs)

    async def delete_one(self, filter):
        to_delete = next(
            (d for d in self.docs if d.get("_id") == filter.get("_id")), None
        )

        class Res:
            deleted_count = 1 if to_delete else 0

        if to_delete:
            self.docs.remove(to_delete)
        return Res()


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    dummy_age = DummyCollection()
    dummy_enr = DummyCollection()
    db = {"age_groups": dummy_age, "enrollments": dummy_enr}

    monkeypatch.setattr(database, "mongo_db", db)
    monkeypatch.setattr(ag_service, "mongo_db", db)
    monkeypatch.setattr(enr_service, "mongo_db", db)
    monkeypatch.setattr(
        RedisProducer, "enqueue_enrollment", lambda self, msg: asyncio.sleep(0)
    )
    return db


client = TestClient(app)


def basic_auth_header():
    creds = (
        f"{settings.BASIC_AUTH_USERNAME}:" f"{settings.BASIC_AUTH_PASSWORD}"
    )
    token = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {token}"}


# 1. Cadastro com sucesso
def test_create_enrollment_success(patch_db):
    db = patch_db
    asyncio.run(
        db["age_groups"].insert_one(
            {"name": "Adulto", "min_age": 18, "max_age": 60}
        )
    )
    payload = {"name": "Fulano", "cpf": "52998224725", "age": 25}
    response = client.post(
        "/api/v1/enrollments/", json=payload, headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["id"] == "em processamento"


# 2. CPF inválido -> 422
def test_create_enrollment_invalid_cpf():
    payload = {"name": "Fulano", "cpf": "abc123", "age": 30}
    response = client.post(
        "/api/v1/enrollments/", json=payload, headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# 3. Idade fora de faixa -> 400
def test_create_enrollment_age_out_of_group(patch_db):
    payload = {"name": "Fulano", "cpf": "52998224725", "age": 5}
    response = client.post(
        "/api/v1/enrollments/", json=payload, headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "nenhum grupo" in response.json()["detail"]


# 4. Duplicidade de CPF -> 400
def test_create_enrollment_duplicate_cpf(patch_db):
    db = patch_db
    asyncio.run(
        db["age_groups"].insert_one(
            {"name": "Adulto", "min_age": 18, "max_age": 60}
        )
    )
    asyncio.run(
        db["enrollments"].insert_one(
            {
                "_id": ObjectId(),
                "name": "Fulano",
                "cpf": "52998224725",
                "age": 30,
            }
        )
    )
    payload = {"name": "Fulano", "cpf": "52998224725", "age": 30}
    response = client.post(
        "/api/v1/enrollments/", json=payload, headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Já existe" in response.json()["detail"]


# 5. Listagem -> 200
def test_list_enrollments(patch_db):
    db = patch_db
    asyncio.run(
        db["enrollments"].insert_one(
            {"_id": ObjectId(), "name": "A", "cpf": "00011122233", "age": 20}
        )
    )
    asyncio.run(
        db["enrollments"].insert_one(
            {"_id": ObjectId(), "name": "B", "cpf": "44455566677", "age": 40}
        )
    )
    response = client.get("/api/v1/enrollments/", headers=basic_auth_header())
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


# 6. Consulta status sucesso -> 200
def test_get_enrollment_status_success(patch_db):
    db = patch_db
    res = asyncio.run(
        db["enrollments"].insert_one(
            {
                "_id": ObjectId(),
                "name": "Fulano",
                "cpf": "52998224725",
                "age": 35,
                "status": "pending",
            }
        )
    )
    eid = str(res.inserted_id)
    response = client.get(
        f"/api/v1/enrollments/{eid}", headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "pending"


# 7. Consulta status não encontrado -> 404
def test_get_enrollment_status_not_found(patch_db):
    fake = str(ObjectId())
    response = client.get(
        f"/api/v1/enrollments/{fake}", headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# 8. ID inválido -> 500
def test_get_enrollment_status_invalid_id(patch_db):
    response = client.get(
        "/api/v1/enrollments/invalid_id", headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
