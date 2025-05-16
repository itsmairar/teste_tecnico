import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.configs import settings

# Define variável de ambiente após os imports
os.environ["MONGO_URI"] = "mongodb://localhost:27017"

# Garante que o diretório raiz esteja no path
sys.path.append(str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def mongo_test_db(monkeypatch):
    client = AsyncIOMotorClient(settings.MONGO_URI)
    test_db = client["test_db"]
    monkeypatch.setattr("app.core.database.mongo_db", test_db)
    yield test_db
    await client.drop_database("test_db")


@pytest.fixture
def redis_mock(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.redis_producer.redis.Redis", lambda *args, **kwargs: mock
    )
    return mock


@pytest.fixture
def token_header():
    return {"Authorization": "Basic YWRtaW46MTIzNDU2"}
