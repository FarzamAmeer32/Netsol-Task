from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ThreadCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    
    model_config = ConfigDict(extra="forbid")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Title cannot be empty.")

        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("Title cannot contain control characters.")

        return value


class ThreadUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    is_archived: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Title cannot be empty.")

        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("Title cannot contain control characters.")

        return value


class ThreadResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ThreadListResponse(BaseModel):
    items: list[ThreadResponse]
    total: int
    limit: int
    offset: int    