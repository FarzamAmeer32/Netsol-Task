from typing import Annotated

from fastapi import APIRouter, Depends

from netsol.api.dependencies import get_llm_service
from netsol.schemas.chat import ChatRequest, ChatResponse, TokenUsage
from netsol.services.llm import LLMService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    llm: Annotated[LLMService, Depends(get_llm_service)],
) -> ChatResponse:
    result = await llm.generate_reply(payload.message)

    return ChatResponse(
        answer=result.answer,
        model=result.model,
        usage=TokenUsage(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )