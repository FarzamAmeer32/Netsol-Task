
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from netsol.core.config import get_settings
from netsol.core.exceptions import ContextMessageTooLargeError
from netsol.graphs.prompts import build_conversation_prompt
from netsol.graphs.state import ChatContextMessage
from netsol.repositories.message import get_recent_messages
from netsol.services.llm import LLMService


CONTEXT_TOKEN_SAFETY_MARGIN = 200


async def build_context(
    db: AsyncSession,
    thread_id: UUID,
    current_message: str,
    llm_service: LLMService,
) -> list[ChatContextMessage]:

    settings = get_settings()

    try:
        database_messages = await get_recent_messages(
            db=db,
            thread_id=thread_id,
            limit=settings.context_max_messages,
        )

        # Convert ORM objects to plain dictionaries before rollback.
        messages: list[ChatContextMessage] = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in database_messages
        ]

    finally:
        # Release the database read transaction.
        await db.rollback()

    # Count the system prompt and current message first.
    base_prompt = build_conversation_prompt(
        context_messages=[],
        user_message=current_message,
    )

    base_tokens = await llm_service.count_tokens(base_prompt)

    if (
        base_tokens + CONTEXT_TOKEN_SAFETY_MARGIN
        > settings.max_context_tokens
    ):
        raise ContextMessageTooLargeError()

    # Find complete user/assistant exchanges, newest first.
    exchanges: list[list[ChatContextMessage]] = []

    index = len(messages) - 1

    while index >= 1:
        if (
            messages[index]["role"] == "assistant"
            and messages[index - 1]["role"] == "user"
        ):
            exchanges.append(
                [
                    messages[index - 1],
                    messages[index],
                ]
            )
            index -= 2
        else:
            index -= 1

    # Add exchanges until the token budget is reached.
    selected_exchanges: list[list[ChatContextMessage]] = []

    for exchange in exchanges:
        candidate_exchanges = [
            exchange,
            *selected_exchanges,
        ]

        candidate_context: list[ChatContextMessage] = [
            message
            for group in candidate_exchanges
            for message in group
        ]

        candidate_prompt = build_conversation_prompt(
            context_messages=candidate_context,
            user_message=current_message,
        )

        candidate_tokens = await llm_service.count_tokens(
            candidate_prompt
        )

        if (
            candidate_tokens + CONTEXT_TOKEN_SAFETY_MARGIN
            > settings.max_context_tokens
        ):
            # Stop instead of skipping an older exchange.
            break

        selected_exchanges = candidate_exchanges

    # Return history in chronological order.
    context_messages: list[ChatContextMessage] = [
        message
        for group in selected_exchanges
        for message in group
    ]

    return context_messages
