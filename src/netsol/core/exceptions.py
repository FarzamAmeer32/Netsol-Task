class LLMUnavailableError(Exception):
    """The LLM provider is unavailable or timed out."""


class LLMRateLimitError(Exception):
    """The LLM provider rate limit was reached."""


class LLMConfigurationError(Exception):
    """The provider authentication or configuration failed."""