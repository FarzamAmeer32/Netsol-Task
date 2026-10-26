from functools import lru_cache

from netsol.services.llm import GeminiLLMService, LLMService


@lru_cache
def get_llm_service() -> LLMService:
    return GeminiLLMService()