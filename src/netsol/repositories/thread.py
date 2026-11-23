import uuid

from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.db.models.thread import ChatThread


async def create_thread(
    db: AsyncSession,
    owner_id: uuid.UUID,
    title: str,
) -> ChatThread:
    thread = ChatThread(
        owner_id=owner_id,
        title=title,
    )

    db.add(thread)

    return thread


async def get_thread_by_id(
    db: AsyncSession,
    thread_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> ChatThread | None:
    result = await db.execute(
        select(ChatThread).where(
            ChatThread.id == thread_id,
            ChatThread.owner_id == owner_id,
        )
    )

    return result.scalar_one_or_none()


async def list_threads(
    db: AsyncSession,
    owner_id: uuid.UUID,
    limit: int,
    offset: int,
    is_archived: bool | None = None,
) -> tuple[list[ChatThread], int]:

    filters = [ChatThread.owner_id == owner_id]

    if is_archived is not None:
        filters.append(ChatThread.is_archived == is_archived)

    count_result = await db.execute(
        select(func.count(ChatThread.id)).where(*filters)
    )

    total = count_result.scalar_one()

    result = await db.execute(
        select(ChatThread)
        .where(*filters)
        .order_by(
            ChatThread.updated_at.desc(),
            ChatThread.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    threads = list(result.scalars().all())

    return threads, total

async def update_thread(
    db: AsyncSession,
    thread: ChatThread,
) -> ChatThread:
    await db.flush()
    return thread

async def delete_thread(
    db: AsyncSession,
    thread: ChatThread,
) -> None:
    await db.delete(thread)