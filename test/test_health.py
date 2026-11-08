
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.app import app
from netsol.db.session import get_db


@pytest.fixture
def client():
    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_success(client):
    fake_db = AsyncMock(spec=AsyncSession)

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "available",
    }

    fake_db.execute.assert_awaited_once()


def test_readiness_check_failure(client):
    fake_db = AsyncMock(spec=AsyncSession)

    fake_db.execute.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health/ready")

    assert response.status_code == 503

    response_data = response.json()

    # Verify that database details are not exposed.
    assert "error" in response_data
    assert "Database connection failed" not in str(response_data)
