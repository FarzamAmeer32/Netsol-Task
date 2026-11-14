import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.db.models.message import ChatMessage
from netsol.db.models.thread import ChatThread

async def create_message(
    db: AsyncSession,
    thread_id: uuid.UUID,
    role: str,
    content: str,
    sequence: int,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> ChatMessage:

    message = ChatMessage(
        thread_id=thread_id,
        role=role,
        content=content,
        sequence=sequence,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    db.add(message)

    return message

async def get_messages(
    db: AsyncSession,
    thread_id: uuid.UUID,
    limit: int,
    after: int | None = None,
) -> tuple[list[ChatMessage], bool]:

    query = select(ChatMessage).where(
        ChatMessage.thread_id == thread_id,
    )

    if after is not None:
        query = query.where(
            ChatMessage.sequence > after,
        )

    query = (
        query
        .order_by(ChatMessage.sequence.asc())
        .limit(limit + 1)
    )

    result = await db.execute(query)

    messages = list(result.scalars().all())

    has_more = len(messages) > limit

    if has_more:
        messages = messages[:limit]

    return messages, has_more    

async def lock_thread(
    db: AsyncSession,
    thread_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> ChatThread | None:

    result = await db.execute(
        select(ChatThread)
        .where(
            ChatThread.id == thread_id,
            ChatThread.owner_id == owner_id,
        )
        .with_for_update()
    )

    return result.scalar_one_or_none()  

async def get_next_sequence(
    db: AsyncSession,
    thread_id: uuid.UUID,
) -> int:

    result = await db.execute(
        select(func.max(ChatMessage.sequence)).where(
            ChatMessage.thread_id == thread_id,
        )
    )

    last_sequence = result.scalar_one()

    return (last_sequence or 0) + 1
  