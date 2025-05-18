"""
Testes para endpoints de Grupos de Idade
"""

import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import base64  # noqa: E402

import pytest  # noqa: E402
from bson import ObjectId  # noqa: E402
from fastapi import status  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.core.database as database  # noqa: E402
import app.services.age_group_service as ag_service  # noqa: E402
from app.core.configs import settings  # noqa: E402
from main import app  # noqa: E402


# Dummy Collection para testes
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
                self._docs = docs
                self._idx = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self._idx >= len(self._docs):
                    raise StopAsyncIteration
                doc = self._docs[self._idx]
                self._idx += 1
                return doc

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
    dummy = DummyCollection()
    db = {"age_groups": dummy}
    monkeypatch.setattr(database, "mongo_db", db)
    monkeypatch.setattr(ag_service, "mongo_db", db)
    return db


client = TestClient(app)


def basic_auth_header():
    credentials = (
        f"{settings.BASIC_AUTH_USERNAME}:" f"{settings.BASIC_AUTH_PASSWORD}"
    )
    token_bytes = credentials.encode()
    token = base64.b64encode(token_bytes).decode()

    return {"Authorization": f"Basic {token}"}


# 1. Criação com sucesso
def test_create_age_group():
    payload = {"name": "Jovem", "min_age": 18, "max_age": 35}
    response = client.post(
        "/api/v1/age-groups/", json=payload, headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["min_age"] == 18
    assert data["max_age"] == 35


# 2. Lista (insere um antes de listar)
def test_list_age_groups():
    client.post(
        "/api/v1/age-groups/",
        json={"name": "Infantil", "min_age": 0, "max_age": 12},
        headers=basic_auth_header(),
    )
    response = client.get("/api/v1/age-groups/", headers=basic_auth_header())
    assert response.status_code == status.HTTP_200_OK
    groups = response.json()
    assert isinstance(groups, list)
    assert len(groups) >= 1


# 3. Exclusão com sucesso
def test_delete_age_group():
    res = client.post(
        "/api/v1/age-groups/",
        json={"name": "Idoso", "min_age": 65, "max_age": 120},
        headers=basic_auth_header(),
    )
    gid = res.json()["id"]
    response = client.delete(
        f"/api/v1/age-groups/{gid}", headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_200_OK


# 4. Erro range inválido -> 422
def test_create_age_group_invalid_range():
    response = client.post(
        "/api/v1/age-groups/",
        json={"name": "X", "min_age": 10, "max_age": 5},
        headers=basic_auth_header(),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert any(
        "min_age deve ser menor que max_age" in err.get("msg", "")
        for err in errors
    )


# 5. Erro sobreposição -> 400
def test_create_age_group_overlap():
    client.post(
        "/api/v1/age-groups/",
        json={"name": "A", "min_age": 20, "max_age": 30},
        headers=basic_auth_header(),
    )
    response = client.post(
        "/api/v1/age-groups/",
        json={"name": "B", "min_age": 25, "max_age": 35},
        headers=basic_auth_header(),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()["detail"]
    assert "sobreposta" in detail["message"]


# 6. Excluir ID inválido -> 400
def test_delete_age_group_invalid_id():
    response = client.delete(
        "/api/v1/age-groups/invalid_id", headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# 7. Excluir não encontrado -> 404
def test_delete_age_group_not_found():
    fake = str(ObjectId())
    response = client.delete(
        f"/api/v1/age-groups/{fake}", headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# 8. Sem auth -> 401
def test_without_auth():
    rv = client.post("/api/v1/age-groups/", json={}, headers={})
    assert rv.status_code == status.HTTP_401_UNAUTHORIZED
    rv = client.get("/api/v1/age-groups/")
    assert rv.status_code == status.HTTP_401_UNAUTHORIZED
    rv = client.delete(f"/api/v1/age-groups/{str(ObjectId())}")
    assert rv.status_code == status.HTTP_401_UNAUTHORIZED
