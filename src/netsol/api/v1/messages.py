
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(tags=["Messages"])

Role = Literal["user", "assistant"]


class MessageCreate(BaseModel):
    role: Role
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Content must not be empty.")
        return value


class MessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Content must not be empty.")
        return value


class MessageResponse(BaseModel):
    id: int
    role: Role
    content: str
    created_at: datetime


# Temporary in-memory storage; data resets when the app restarts.
messages: dict[int, MessageResponse] = {}
next_message_id = 1


def get_message_or_404(message_id: int) -> MessageResponse:
    message = messages.get(message_id)

    if message is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "not_found",
                "message": f"Message with ID {message_id} was not found.",
            },
        )

    return message


@router.post(
    "/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(payload: MessageCreate):
    global next_message_id

    message = MessageResponse(
        id=next_message_id,
        role=payload.role,
        content=payload.content,
        created_at=datetime.now(timezone.utc),
    )

    messages[next_message_id] = message
    next_message_id += 1

    return message


@router.get("/messages", response_model=list[MessageResponse])
async def list_messages(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    role: Role | None = Query(default=None),
):
    results = list(messages.values())

    if role is not None:
        results = [item for item in results if item.role == role]

    # Newest messages first.
    results.reverse()

    return results[offset : offset + limit]


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def read_message(message_id: int):
    return get_message_or_404(message_id)


@router.patch("/messages/{message_id}", response_model=MessageResponse)
async def update_message(message_id: int, payload: MessageUpdate):
    existing = get_message_or_404(message_id)

    updated = existing.model_copy(update={"content": payload.content})
    messages[message_id] = updated

    return updated


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_message(message_id: int):
    get_message_or_404(message_id)
    del messages[message_id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)
