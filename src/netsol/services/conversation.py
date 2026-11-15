from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.db.models.message import ChatMessage

from netsol.repositories.message import (
    create_message as create_message_record,
    get_messages as get_message_records,
    get_next_sequence,
    lock_thread,
)
from netsol.repositories.thread import get_thread_by_id
from typing import Any

from netsol.services.llm import LLMResult

class ConversationOperationError(Exception):
    pass


class ConversationThreadNotFoundError(Exception):
    pass


class ConversationThreadArchivedError(Exception):
    pass

async def get_conversation_messages(
    db: AsyncSession,
    thread_id: UUID,
    owner_id: UUID,
    limit: int,
    after: int | None = None,
) -> tuple[list[ChatMessage], int | None, bool]:

    try:
        thread = await get_thread_by_id(
            db=db,
            thread_id=thread_id,
            owner_id=owner_id,
        )

        if thread is None:
            raise ConversationThreadNotFoundError

        messages, has_more = await get_message_records(
            db=db,
            thread_id=thread_id,
            limit=limit,
            after=after,
        )

        next_cursor = messages[-1].sequence if has_more and messages else None

        return messages, next_cursor, has_more

    except ConversationThreadNotFoundError:
        raise

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ConversationOperationError from exc

async def validate_thread_for_message(
    db: AsyncSession,
    thread_id: UUID,
    owner_id: UUID,
) -> None:

    try:
        thread = await get_thread_by_id(
            db=db,
            thread_id=thread_id,
            owner_id=owner_id,
        )

        if thread is None:
            await db.rollback()
            raise ConversationThreadNotFoundError

        if thread.is_archived:
            await db.rollback()
            raise ConversationThreadArchivedError

        # Release the read transaction before calling the LLM.
        await db.rollback()

    except (
        ConversationThreadNotFoundError,
        ConversationThreadArchivedError,
    ):
        raise

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ConversationOperationError from exc    

async def send_message(
    db: AsyncSession,
    chat_graph: Any,
    thread_id: UUID,
    owner_id: UUID,
    content: str,
) -> tuple[ChatMessage, ChatMessage]:

    await validate_thread_for_message(
        db=db,
        thread_id=thread_id,
        owner_id=owner_id,
    )

    # Generate the assistant reply before starting the write transaction.
    graph_result = await chat_graph.ainvoke({"user_message": content})
    result = LLMResult(
    answer=graph_result["answer"],
    model=graph_result["model"],
    input_tokens=graph_result.get("input_tokens"),
    output_tokens=graph_result.get("output_tokens"),)

    try:
        async with db.begin():
            thread = await lock_thread(
                db=db,
                thread_id=thread_id,
                owner_id=owner_id,
            )

            if thread is None:
                raise ConversationThreadNotFoundError

            if thread.is_archived:
                raise ConversationThreadArchivedError

            user_sequence = await get_next_sequence(
                db=db,
                thread_id=thread_id,
            )

            user_message = await create_message_record(
                db=db,
                thread_id=thread_id,
                role="user",
                content=content,
                sequence=user_sequence,
            )

            assistant_message = await create_message_record(
                db=db,
                thread_id=thread_id,
                role="assistant",
                content=result.answer,
                sequence=user_sequence + 1,
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            )

            thread.updated_at = datetime.now(timezone.utc)

            await db.flush()

        await db.refresh(user_message)
        await db.refresh(assistant_message)

        return user_message, assistant_message

    except (
        ConversationThreadNotFoundError,
        ConversationThreadArchivedError,
    ):
        raise

    except SQLAlchemyError as exc:
        await db.rollback()
        raise ConversationOperationError from exc    