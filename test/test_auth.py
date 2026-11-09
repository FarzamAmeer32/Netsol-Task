
import asyncio
import uuid
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.core.security import verify_password
from netsol.db.models.user import User
from netsol.services import user as user_service


def test_register_user_success(auth_client):
    email = f"{uuid.uuid4()}@example.com"
    password = "MyStrongPass!2026"

    response = auth_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == email
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_user_is_persisted_with_hashed_password(
    auth_client,
    test_engine,
):
    email = f"{uuid.uuid4()}@example.com"
    password = "MyStrongPass!2026"

    response = auth_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    assert response.status_code == 201

    async def get_saved_user():
        async with AsyncSession(
            test_engine,
            expire_on_commit=False,
        ) as db:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()

    saved_user = asyncio.run(get_saved_user())

    assert saved_user is not None
    assert saved_user.password_hash != password
    assert verify_password(password, saved_user.password_hash)


def test_register_rejects_invalid_email(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "MyStrongPass!2026",
        },
    )

    assert response.status_code == 422


def test_register_rejects_short_password(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid.uuid4()}@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_register_rejects_long_password(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid.uuid4()}@example.com",
            "password": "A" * 129,
        },
    )

    assert response.status_code == 422


def test_register_rejects_weak_password(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid.uuid4()}@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_normalizes_email_domain(auth_client):
    email = f"Farzam-{uuid.uuid4()}@EXAMPLE.COM"
    expected_email = email.replace("@EXAMPLE.COM", "@example.com")

    response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "MyStrongPass!2026",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == expected_email


def test_register_rejects_duplicate_email(auth_client):
    email = f"{uuid.uuid4()}@EXAMPLE.COM"
    password = "MyStrongPass!2026"

    first_response = auth_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    second_response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": email.lower(),
            "password": password,
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_registration_response_excludes_password_fields(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid.uuid4()}@example.com",
            "password": "MyStrongPass!2026",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert "password" not in response_data
    assert "password_hash" not in response_data
    assert "hashed_password" not in response_data


@pytest.mark.asyncio
async def test_registration_rolls_back_on_integrity_error():
    from sqlalchemy.exc import IntegrityError

    class FakeSession:
        def __init__(self):
            self.rolled_back = False

        async def commit(self):
            raise IntegrityError(
                "INSERT",
                {},
                Exception("simulated integrity error"),
            )

        async def rollback(self):
            self.rolled_back = True

    fake_db = FakeSession()

    with patch.object(
        user_service,
        "get_user_by_email",
        new_callable=AsyncMock,
        return_value=None,
    ), patch.object(
        user_service,
        "create_user",
        new_callable=AsyncMock,
        return_value=object(),
    ), patch.object(
        user_service,
        "hash_password",
        return_value="fake-hash",
    ), patch.object(
        user_service,
        "is_duplicate_email_error",
        return_value=False,
    ):
        with pytest.raises(user_service.UserRegistrationError):
            await user_service.register_user(
                fake_db,
                "rollback@example.com",
                "MyStrongPass!2026",
            )

    assert fake_db.rolled_back is True


def test_database_error_returns_safe_503(auth_client):
    with patch.object(
        user_service,
        "get_user_by_email",
        new_callable=AsyncMock,
        side_effect=SQLAlchemyError(
            "secret database connection details"
        ),
    ):
        response = auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"{uuid.uuid4()}@example.com",
                "password": "MyStrongPass!2026",
            },
        )

    assert response.status_code == 503
    assert "secret database connection details" not in response.text
    assert response.json()["error"]["code"] == "http_error"
    assert response.json()["error"]["request_id"]
    assert response.headers["X-Request-ID"]

@pytest.mark.asyncio
async def test_concurrent_registration_allows_only_one_user(test_engine):
    email = f"{uuid.uuid4()}@example.com"
    password = "MyStrongPass!2026"

    session_factory = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

    async def register():
        async with session_factory() as db:
            try:
                return await user_service.register_user(
                    db,
                    email,
                    password,
                )
            except user_service.EmailAlreadyRegisteredError as exc:
                return exc

    results = await asyncio.gather(
        register(),
        register(),
    )

    successful = [
        result for result in results
        if isinstance(result, User)
    ]

    conflicts = [
        result for result in results
        if isinstance(result, user_service.EmailAlreadyRegisteredError)
    ]

    assert len(successful) == 1
    assert len(conflicts) == 1

    async with session_factory() as db:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        saved_users = result.scalars().all()

    assert len(saved_users) == 1