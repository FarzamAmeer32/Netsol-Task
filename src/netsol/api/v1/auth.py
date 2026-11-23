
from fastapi import APIRouter, HTTPException, status

from netsol.schemas.auth import LoginRequest, TokenResponse
from netsol.services.auth import InvalidCredentialsError, login_user
from netsol.core.config import get_settings

from netsol.api.dependencies import DbSession
from netsol.schemas.user import UserRegister, UserResponse
from netsol.services.user import (
    EmailAlreadyRegisteredError,
    UserRegistrationError,
    register_user,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister,
    db: DbSession,
):
    try:
        user = await register_user(
            db=db,
            email=str(payload.email),
            password=payload.password,
        )

        return user

    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    except UserRegistrationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration is temporarily unavailable.",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    db: DbSession,
):
    try:
        access_token = await login_user(
            db=db,
            email=str(payload.email),
            password=payload.password,
        )

        settings = get_settings()

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_credentials",
                "message": "Email or password is incorrect.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
