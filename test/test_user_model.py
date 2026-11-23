
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from netsol.db.models.user import User
from netsol.db.session import AsyncSessionLocal


@pytest.mark.asyncio
async def test_user_email_must_be_unique():

    email = f"{uuid.uuid4()}@example.com"

    async with AsyncSessionLocal() as db:

        first_user = User(
            email=email,
            password_hash="test_hash_1",
        )

        db.add(first_user)
        await db.commit()

        second_user = User(
            email=email,
            password_hash="test_hash_2",
        )

        db.add(second_user)

        with pytest.raises(IntegrityError):
            await db.commit()

        await db.rollback()

        await db.delete(first_user)
        await db.commit()
