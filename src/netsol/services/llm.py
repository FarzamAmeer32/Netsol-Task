import asyncio
from dataclasses import dataclass
from typing import Protocol

from google import genai
from google.genai import errors, types

from netsol.core.config import get_settings
from netsol.core.exceptions import (
    LLMConfigurationError,
    LLMRateLimitError,
    LLMUnavailableError,
)


@dataclass
class LLMResult:
    answer: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


class LLMService(Protocol):
    async def generate_reply(self, message: str) -> LLMResult:
        ...


class GeminiLLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

        self.client = genai.Client(
            api_key=self.settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=int(self.settings.llm_timeout_seconds * 1000)
            ),
        )

    async def generate_reply(self, message: str) -> LLMResult:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.settings.llm_model,
                contents=message,
                config=types.GenerateContentConfig(
                    max_output_tokens=self.settings.llm_max_output_tokens,
                ),
            )
        except errors.ClientError as exc:
            if exc.code == 429:
                raise LLMRateLimitError() from None

            if exc.code in (401, 403):
                raise LLMConfigurationError() from None

            raise LLMUnavailableError() from None
        except (
            errors.ServerError,
            TimeoutError,
            asyncio.TimeoutError,
        ):
            raise LLMUnavailableError() from None
        except Exception:
            # Don't expose provider details to the client.
            raise LLMUnavailableError() from None

        answer = response.text

        if not answer or not answer.strip():
            raise LLMUnavailableError()

        usage = response.usage_metadata

        return LLMResult(
            answer=answer.strip(),
            model=self.settings.llm_model,
            input_tokens=(
                getattr(usage, "prompt_token_count", None)
                if usage else None
            ),
            output_tokens=(
                getattr(usage, "candidates_token_count", None)
                if usage else None
            ),
        )