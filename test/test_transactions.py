
import uuid

import pytest

from netsol.db.models.user import User
from netsol.db.session import AsyncSessionLocal


@pytest.mark.asyncio
async def test_transaction_rollback():

    email = f"{uuid.uuid4()}@example.com"

    async with AsyncSessionLocal() as db:

        user = User(
            email=email,
            password_hash="test_hash",
        )

        db.add(user)

        # Roll back before committing.
        await db.rollback()

    # Check that the user was not saved.
    async with AsyncSessionLocal() as db:

        from sqlalchemy import select

        result = await db.execute(
            select(User).where(User.email == email)
        )

        saved_user = result.scalar_one_or_none()

        assert saved_user is None
