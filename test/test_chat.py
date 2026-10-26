
import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient

from netsol.app import app
from netsol.api.dependencies import get_llm_service
from netsol.core.exceptions import (
    LLMConfigurationError,
    LLMRateLimitError,
    LLMUnavailableError,
)
from netsol.services.llm import LLMResult


class FakeLLMService:
    """A fake LLM service for testing without Gemini API calls."""

    def __init__(self, error=None):
        self.error = error

    async def generate_reply(self, message: str) -> LLMResult:
        if self.error is not None:
            raise self.error

        return LLMResult(
            answer=f"Test reply to: {message}",
            model="fake-model",
            input_tokens=5,
            output_tokens=10,
        )


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_chat_success():
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService()
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 200

    data = response.json()
    assert data["answer"] == "Test reply to: Hello"
    assert data["model"] == "fake-model"
    assert data["usage"]["input_tokens"] == 5
    assert data["usage"]["output_tokens"] == 10


def test_chat_returns_request_id():
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService()
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            headers={"X-Request-ID": "chat-test-123"},
            json={"message": "Hello"},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "chat-test-123"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "    "},
        {"message": "x" * 4001},
    ],
)
def test_chat_rejects_invalid_input(payload):
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService()
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json=payload,
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_chat_handles_llm_unavailable():
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService(error=LLMUnavailableError())
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "llm_unavailable"
    assert response.json()["error"]["request_id"]


def test_chat_handles_rate_limit():
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService(error=LLMRateLimitError())
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "llm_rate_limited"


def test_chat_handles_configuration_error():
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService(error=LLMConfigurationError())
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 503
    assert (
        response.json()["error"]["code"]
        == "llm_configuration_error"
    )
