
import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault("GEMINI_API_KEY", "test-key")

from netsol.app import app
from netsol.api.dependencies import get_checkpointer
from netsol.core.config import get_settings
from netsol.db.base import Base
from netsol.db.models.user import User
from netsol.db.session import get_db


class FakeCheckpointer:

    def __init__(self):
        self.deleted_thread_ids = []

    async def adelete_thread(self, thread_id: str) -> None:
        self.deleted_thread_ids.append(thread_id)


@pytest.fixture
def fake_checkpointer():
    return FakeCheckpointer()


@pytest.fixture
def test_engine():
    test_url = os.getenv("TEST_DATABASE_URL")

    if test_url:
        database_url = make_url(test_url)
    else:
        database_url = make_url(get_settings().database_url).set(
            database="netsol_test"
        )

    if database_url.database != "netsol_test":
        raise RuntimeError(
            "Tests must use the dedicated netsol_test database."
        )

    engine = create_async_engine(
        database_url,
        poolclass=NullPool,
        echo=False,
    )

    async def create_tables():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(create_tables())

    yield engine

    async def remove_tables():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)

    asyncio.run(remove_tables())
    asyncio.run(engine.dispose())


@pytest.fixture
def auth_client(test_engine, fake_checkpointer):

    async def override_get_db():
        async with AsyncSession(
            test_engine,
            expire_on_commit=False,
        ) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    app.dependency_overrides[get_checkpointer] = (
        lambda: fake_checkpointer
    )

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_checkpointer, None)
