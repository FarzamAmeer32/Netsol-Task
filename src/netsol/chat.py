


from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from netsol.llm_service import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMUnavailableError,
    generate_reply,
)

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be empty or whitespace.")
        return value


class TokenUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None


class ChatResponse(BaseModel):
    answer: str
    model: str
    usage: TokenUsage


@router.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    summary="Generate an AI response",
    responses={
        401: {"description": "LLM provider authentication failed"},
        429: {"description": "LLM provider rate limit reached"},
        503: {"description": "LLM provider unavailable or timed out"},
    },
)
async def chat(payload: ChatRequest) -> ChatResponse:
    try:
        result = await generate_reply(payload.message)
    except LLMAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider authentication failed. Check server configuration.",
        ) from None
    except LLMRateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="LLM provider rate limit reached. Please try again later.",
        ) from None
    except LLMUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider is temporarily unavailable. Please try again.",
        ) from None

    return ChatResponse(
        answer=result.answer,
        model=result.model,
        usage=TokenUsage(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )
