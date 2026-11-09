
from fastapi import APIRouter, HTTPException, status

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
