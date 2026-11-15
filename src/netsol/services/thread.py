
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.db.models.thread import ChatThread
from netsol.repositories.thread import (
    create_thread as create_thread_record,
    delete_thread as delete_thread_record,
    get_thread_by_id,
    list_threads as list_thread_records,
    update_thread as update_thread_record,
)


class ThreadOperationError(Exception):
    pass


class ThreadNotFoundError(Exception):
    pass


class EmptyThreadUpdateError(Exception):
    pass


class InvalidThreadUpdateError(Exception):
    pass


async def create_thread(
    db: AsyncSession,
    owner_id,
    title: str,
) -> ChatThread:
    try:
        thread = await create_thread_record(
            db,
            owner_id,
            title,
        )

        await db.commit()
        await db.refresh(thread)

        return thread

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ThreadOperationError from exc


async def get_threads(
    db: AsyncSession,
    owner_id,
    limit: int,
    offset: int,
    is_archived: bool | None = None,
) -> tuple[list[ChatThread], int]:
    try:
        return await list_thread_records(
            db=db,
            owner_id=owner_id,
            limit=limit,
            offset=offset,
            is_archived=is_archived,
        )

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ThreadOperationError from exc


async def get_thread(
    db: AsyncSession,
    thread_id,
    owner_id,
) -> ChatThread:
    try:
        thread = await get_thread_by_id(
            db=db,
            thread_id=thread_id,
            owner_id=owner_id,
        )

        if thread is None:
            raise ThreadNotFoundError

        return thread

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ThreadOperationError from exc


async def update_thread(
    db: AsyncSession,
    thread_id: UUID,
    owner_id: UUID,
    updates: dict,
) -> ChatThread:

    if not updates:
        raise EmptyThreadUpdateError

    allowed_fields = {"title", "is_archived"}

    if not updates.keys() <= allowed_fields:
        raise InvalidThreadUpdateError

    if any(value is None for value in updates.values()):
        raise InvalidThreadUpdateError

    try:
        thread = await get_thread(
            db=db,
            thread_id=thread_id,
            owner_id=owner_id,
        )

        changed = False

        if "title" in updates:
            if thread.title != updates["title"]:
                thread.title = updates["title"]
                changed = True

        if "is_archived" in updates:
            if thread.is_archived != updates["is_archived"]:
                thread.is_archived = updates["is_archived"]
                changed = True

        if changed:
            thread.updated_at = datetime.now(timezone.utc)

            await update_thread_record(db, thread)

            await db.commit()
            await db.refresh(thread)

        return thread

    except ThreadOperationError:
        raise

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ThreadOperationError from exc


async def delete_thread(
    db: AsyncSession,
    thread_id: UUID,
    owner_id: UUID,
    checkpointer: Any,
) -> None:

    try:
        # First verify that this thread belongs to the requesting user.
        thread = await get_thread(
            db=db,
            thread_id=thread_id,
            owner_id=owner_id,
        )

        # Build the same namespaced ID used by LangGraph.
        graph_thread_id = f"chat:{owner_id}:{thread_id}"

        # Delete the LangGraph checkpoint.
        await checkpointer.adelete_thread(graph_thread_id)

        # Delete the application thread and its messages.
        await delete_thread_record(db, thread)

        await db.commit()

    except ThreadOperationError:
        raise

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ThreadOperationError from exc
