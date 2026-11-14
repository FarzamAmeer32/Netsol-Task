from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from netsol.api.dependencies import DbSession, get_current_user
from netsol.db.models.user import User
from netsol.schemas.thread import (
    ThreadCreate,
    ThreadListResponse,
    ThreadResponse,
    ThreadUpdate,
)
from netsol.services.thread import (
    EmptyThreadUpdateError,
    InvalidThreadUpdateError,
    ThreadNotFoundError,
    create_thread,
    delete_thread,
    get_thread,
    get_threads,
    update_thread,
)

router = APIRouter(prefix="/threads", tags=["Threads"])


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


@router.post(
    "",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_thread(
    payload: ThreadCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    thread = await create_thread(
        db=db,
        owner_id=current_user.id,
        title=payload.title,
    )

    return thread

@router.get(
    "",
    response_model=ThreadListResponse,
)
async def list_chat_threads(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    is_archived: bool | None = Query(default=None),
):
    threads, total = await get_threads(
        db=db,
        owner_id=current_user.id,
        limit=limit,
        offset=offset,
        is_archived=is_archived,
    )

    return ThreadListResponse(
        items=threads,
        total=total,
        limit=limit,
        offset=offset,
    )

@router.get(
    "/{thread_id}",
    response_model=ThreadResponse,
)
async def read_chat_thread(
    thread_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    try:
        return await get_thread(
            db=db,
            thread_id=thread_id,
            owner_id=current_user.id,
        )

    except ThreadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "thread_not_found",
                "message": "Chat thread was not found.",
            },
        )

@router.patch(
    "/{thread_id}",
    response_model=ThreadResponse,
)
async def update_chat_thread(
    thread_id: UUID,
    payload: ThreadUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    try:
        updates = payload.model_dump(exclude_unset=True)

        return await update_thread(
            db=db,
            thread_id=thread_id,
            owner_id=current_user.id,
            updates=updates,
        )

    except ThreadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "thread_not_found",
                "message": "Chat thread was not found.",
            },
        )

    except (EmptyThreadUpdateError, InvalidThreadUpdateError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "invalid_thread_update",
                "message": "Provide a valid title or archive status to update.",
            },
        )        

@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat_thread(
    thread_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    try:
        await delete_thread(
            db=db,
            thread_id=thread_id,
            owner_id=current_user.id,
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ThreadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "thread_not_found",
                "message": "Chat thread was not found.",
            },
        )    