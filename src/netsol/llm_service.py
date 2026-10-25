
import asyncio
from dataclasses import dataclass

from google import genai
from google.genai import errors, types

from netsol.config import settings

import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    answer: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


client = genai.Client(
    api_key=settings.gemini_api_key,
    http_options=types.HttpOptions(
        timeout=int(settings.llm_timeout_seconds * 1000)
    ),
)


async def generate_reply(message: str) -> LLMResult:
    try:
        response = await client.aio.models.generate_content(
            model=settings.llm_model,
            contents=message,
            config=types.GenerateContentConfig(
                max_output_tokens=settings.llm_max_output_tokens,
            ),
        )
    except errors.ClientError as exc:
        if exc.code == 429:
            raise LLMRateLimitError() from None
        if exc.code in (401, 403):
            raise LLMAuthenticationError() from None
        raise LLMUnavailableError() from None
    except (errors.ServerError, TimeoutError, asyncio.TimeoutError):
        raise LLMUnavailableError() from None
    except Exception as exc:
        logger.error(
        "LLM request failed. Exception type: %s",
        type(exc).__name__,
     )
        raise LLMUnavailableError() from None

    answer = response.text
    if not answer or not answer.strip():
        raise LLMUnavailableError()

    usage = response.usage_metadata

    return LLMResult(
        answer=answer.strip(),
        model=settings.llm_model,
        input_tokens=(
            getattr(usage, "prompt_token_count", None) if usage else None
        ),
        output_tokens=(
            getattr(usage, "candidates_token_count", None) if usage else None
        ),
    )


class LLMAuthenticationError(Exception):
    pass


class LLMRateLimitError(Exception):
    pass


class LLMUnavailableError(Exception):
    pass
