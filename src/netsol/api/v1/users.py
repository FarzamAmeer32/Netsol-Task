from typing import Annotated

from fastapi import APIRouter, Depends

from netsol.api.dependencies import get_current_user
from netsol.db.models.user import User
from netsol.schemas.user import UserResponse


router = APIRouter(prefix="/users", tags=["Users"])


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: CurrentUser,
):
    return current_user