
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    llm_model: str = "gemini-3.8-flash"
    llm_timeout_seconds: float = 30.0
    llm_max_output_tokens: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
