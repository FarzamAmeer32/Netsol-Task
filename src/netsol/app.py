
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator


app = FastAPI(
    title="Python API Starter",
    version="0.2.0",
    description="A simple in-memory Messages API.",
)


# ---------- Request and response models ----------

class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Content must not be empty or whitespace.")

        return value


class MessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Content must not be empty or whitespace.")

        return value


class MessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str


# ---------- In-memory storage ----------

messages: list[dict] = []
next_message_id = 1


# ---------- Helper function ----------

def find_message(message_id: int) -> dict:
    for message in messages:
        if message["id"] == message_id:
            return message

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Message with ID {message_id} not found.",
    )


# ---------- API endpoints ----------

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": app.version}


@app.post(
    "/api/v1/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Messages"],
    summary="Create a message",
    description="Create a user or assistant message.",
    responses={422: {"description": "Invalid message data"}},
)
def create_message(payload: MessageCreate):
    global next_message_id

    message = {
        "id": next_message_id,
        "role": payload.role,
        "content": payload.content,
        "created_at": datetime.now(timezone.utc),
    }

    messages.append(message)
    next_message_id += 1

    return message


@app.get(
    "/api/v1/messages",
    response_model=list[MessageResponse],
    tags=["Messages"],
    summary="List messages",
    description="List messages with pagination and optional role filtering.",
)
def list_messages(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    role: Literal["user", "assistant"] | None = Query(default=None),
):
    result = messages

    if role is not None:
        result = [m for m in result if m["role"] == role]

    return result[offset:offset + limit]


@app.get(
    "/api/v1/messages/{message_id}",
    response_model=MessageResponse,
    tags=["Messages"],
    summary="Get a message",
    responses={404: {"model": ErrorResponse, "description": "Message not found"}},
)
def get_message(message_id: int):
    return find_message(message_id)


@app.patch(
    "/api/v1/messages/{message_id}",
    response_model=MessageResponse,
    tags=["Messages"],
    summary="Update a message",
    responses={
        404: {"model": ErrorResponse, "description": "Message not found"},
        422: {"description": "Invalid message content"},
    },
)
def update_message(message_id: int, payload: MessageUpdate):
    message = find_message(message_id)
    message["content"] = payload.content

    return message


@app.delete(
    "/api/v1/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Messages"],
    summary="Delete a message",
    responses={404: {"model": ErrorResponse, "description": "Message not found"}},
)
def delete_message(message_id: int):
    message = find_message(message_id)
    messages.remove(message)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
