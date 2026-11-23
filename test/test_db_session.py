
from unittest.mock import AsyncMock, patch

import pytest

from netsol.db.session import get_db


@pytest.mark.asyncio
async def test_get_db_session_lifecycle():
    fake_session = AsyncMock()
    session_context = AsyncMock()
    session_context.__aenter__.return_value = fake_session

    with patch(
        "netsol.db.session.AsyncSessionLocal",
        return_value=session_context,
    ):
        generator = get_db()

        session = await anext(generator)

        assert session is fake_session

        await generator.aclose()

        session_context.__aexit__.assert_awaited_once()
