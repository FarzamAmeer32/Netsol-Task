from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = Field(min_length=1)
    llm_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: float = Field(default=30, gt=0)
    llm_max_input_chars: int = Field(default=4000, gt=0)
    llm_max_output_tokens: int = Field(default=300, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()