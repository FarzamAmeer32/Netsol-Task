from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.db.session import get_db
from netsol.services.llm import GeminiLLMService, LLMService


@lru_cache
def get_llm_service() -> LLMService:
    return GeminiLLMService()


DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]