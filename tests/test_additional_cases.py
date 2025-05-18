'''
Testes adicionais cobrindo casos de erro e autenticação
'''

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import base64
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from bson import ObjectId

from main import app
from app.core.configs import settings
import app.core.database as database
import app.services.age_group_service as ag_service

client = TestClient(app)


def basic_auth_header():
    token = base64.b64encode(
        f"{settings.BASIC_AUTH_USERNAME}:{settings.BASIC_AUTH_PASSWORD}".encode()
    ).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    class DummyCollection:
        def __init__(self): self.docs = []

        async def insert_one(self, doc):
            doc.setdefault('_id', ObjectId())
            self.docs.append(doc)
            class Res: inserted_id = doc['_id']
            return Res()

        async def find_one(self, f):
            for d in self.docs:
                if all((d.get(k) == v) if not isinstance(v, dict) else True for k,v in f.items()):
                    return d
            return None

        def find(self, f):
            class Ctx:
                def __init__(self, docs): self.docs, self.i = docs, 0
                def __aiter__(self): return self

                async def __anext__(self):
                    if self.i >= len(self.docs): raise StopAsyncIteration
                    d = self.docs[self.i]; self.i += 1; return d
            return Ctx(self.docs)

        async def delete_one(self, f):
            target = next((d for d in self.docs if d.get('_id') == f.get('_id')), None)
            class Res: deleted_count = 1 if target else 0
            if target: self.docs.remove(target)
            return Res()
    db = {'age_groups': DummyCollection(), 'enrollments': DummyCollection()}
    monkeypatch.setattr(database, 'mongo_db', db)
    monkeypatch.setattr(ag_service, 'mongo_db', db)
    yield db


# 1. Criar grupo inválido (min_age >= max_age)
def test_create_age_group_invalid_range():
    response = client.post(
        '/api/v1/age-groups/',
        json={'name':'X','min_age':10,'max_age':5},
        headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()['detail']
    assert any('min_age deve ser menor que max_age' in err.get('msg','') for err in errors)


# 2. Criar faixa sobreposta
def test_create_age_group_overlap(patch_db):
    db = patch_db
    import asyncio
    asyncio.run(db['age_groups'].insert_one({'name':'Adulto','min_age':18,'max_age':60}))
    response = client.post(
        '/api/v1/age-groups/',
        json={'name':'JovemAdulto','min_age':30,'max_age':40},
        headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()['detail']
    assert detail['message'].startswith('Faixa etária sobreposta')


# 3. Deletar grupo: ID inválido
def test_delete_age_group_invalid_id():
    response = client.delete(
        '/api/v1/age-groups/invalid', headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'ID inválido'


# 4. Deletar grupo: não encontrado
def test_delete_age_group_not_found():
    fake = str(ObjectId())
    response = client.delete(
        f'/api/v1/age-groups/{fake}', headers=basic_auth_header()
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Grupo de idade não encontrado'


# 5. Autenticação para endpoints sem header ou com credenciais erradas
@pytest.mark.parametrize('method,endpoint,json_payload', [
    ('post','/api/v1/age-groups/',{'name':'T','min_age':1,'max_age':2}),
    ('get','/api/v1/age-groups/',None),
    ('delete','/api/v1/age-groups/'+str(ObjectId()),None),
    ('post','/api/v1/enrollments/',{'name':'A','cpf':'52998224725','age':20}),
    ('get','/api/v1/enrollments/',None),
    ('get','/api/v1/enrollments/'+str(ObjectId()),None),
])
def test_unauthorized_access(method, endpoint, json_payload):
    func = getattr(client, method)
    r1 = func(endpoint, json=json_payload) if json_payload else func(endpoint)
    assert r1.status_code == status.HTTP_401_UNAUTHORIZED
    wrong = base64.b64encode(b'foo:bar').decode()
    headers = {'Authorization': f'Basic {wrong}'}
    r2 = func(endpoint, json=json_payload, headers=headers) if json_payload else func(endpoint, headers=headers)
    assert r2.status_code == status.HTTP_401_UNAUTHORIZED
