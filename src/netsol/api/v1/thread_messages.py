from typing import Annotated,Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from netsol.api.dependencies import (
    DbSession,
    get_current_user,
    get_chat_graph,
)
from netsol.db.models.user import User
from netsol.schemas.message import (
    MessageCreate,
    MessageListResponse,
    MessagePairResponse,
)

from netsol.services.conversation import (
    ConversationOperationError,
    ConversationThreadArchivedError,
    ConversationThreadNotFoundError,
    get_conversation_messages,
    send_message,
)
from netsol.core.exceptions import (
    LLMConfigurationError,
    LLMRateLimitError,
    LLMUnavailableError,
    LLMResponseValidationError,
)

router = APIRouter(prefix="/threads", tags=["Messages"])


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


chat_graph = Annotated[Any, Depends(get_chat_graph)]  

@router.post(
    "/{thread_id}/messages",
    response_model=MessagePairResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread_message(
    thread_id: UUID,
    payload: MessageCreate,
    db: DbSession,
    current_user: CurrentUser,
    chat_graph: chat_graph,
) -> MessagePairResponse:

    try:
        user_message, assistant_message = await send_message(
            db=db,
            chat_graph=chat_graph,
            thread_id=thread_id,
            owner_id=current_user.id,
            content=payload.content,
        )
    

    except ConversationThreadNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "thread_not_found",
                "message": "Thread not found.",
            },
        )

    except ConversationThreadArchivedError:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "thread_archived",
                "message": "Cannot send messages to an archived thread.",
            },
        )

    except LLMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "llm_rate_limited",
                "message": "AI service rate limit reached. Try again later.",
            },
        )

    except (LLMUnavailableError, LLMConfigurationError):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "llm_unavailable",
                "message": "AI service is temporarily unavailable.",
            },
        )
    except LLMResponseValidationError:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "invalid_llm_response",
                    "message": "The AI service returned an unusable response.",
                },
            )
    
    except ConversationOperationError:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "conversation_error",
                "message": "Could not process the conversation.",
            },
        )

    return MessagePairResponse(
        user_message=user_message,
        assistant_message=assistant_message,
    )

@router.get(
    "/{thread_id}/messages",
    response_model=MessageListResponse,
)
async def list_thread_messages(
    thread_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    after: int | None = Query(default=None, ge=0),
) -> MessageListResponse:

    try:
        messages, next_cursor, has_more = await get_conversation_messages(
            db=db,
            thread_id=thread_id,
            owner_id=current_user.id,
            limit=limit,
            after=after,
        )

    except ConversationThreadNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "thread_not_found",
                "message": "Thread not found.",
            },
        )

    except ConversationOperationError:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "conversation_error",
                "message": "Could not retrieve conversation history.",
            },
        )

    return MessageListResponse(
        items=messages,
        limit=limit,
        next_cursor=next_cursor,
        has_more=has_more,
    )    