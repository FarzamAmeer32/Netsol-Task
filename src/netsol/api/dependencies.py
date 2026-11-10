from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.db.session import get_db
from netsol.services.llm import GeminiLLMService, LLMService

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import uuid

import jwt

from netsol.core.security import decode_access_token
from netsol.repositories.user import get_user_by_id


@lru_cache
def get_llm_service() -> LLMService:
    return GeminiLLMService()


DbSession = Annotated[
    AsyncSession,
    Depends(get_db),
]

bearer_scheme = HTTPBearer(auto_error=False)

def unauthorized_error():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "unauthorized",
            "message": "Authentication is required or the access token is invalid.",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: DbSession,
):
    if credentials is None:
        raise unauthorized_error()

    try:
        payload = decode_access_token(credentials.credentials)

        if payload.get("type") != "access":
            raise unauthorized_error()

        user_id = uuid.UUID(payload["sub"])

    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise unauthorized_error()

    user = await get_user_by_id(
        db,
        user_id,
    )

    if user is None or not user.is_active:
        raise unauthorized_error()

    return user