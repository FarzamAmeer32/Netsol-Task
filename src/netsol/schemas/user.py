
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def reject_weak_passwords(cls, value: str) -> str:
        weak_passwords = {
            "password123",
            "1234567890",
            "qwerty12345",
            "abcdefghij",
        }

        if value.casefold() in weak_passwords:
            raise ValueError("Choose a stronger password.")

        return value


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
