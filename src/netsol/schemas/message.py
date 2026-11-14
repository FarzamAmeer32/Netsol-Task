from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message must not be empty or whitespace.")

        if not any(char.isprintable() and not char.isspace() for char in value):
            raise ValueError("Message must contain visible characters.")

        return value


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    sequence: int
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    created_at: datetime


class MessagePairResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    limit: int
    next_cursor: int | None
    has_more: bool    