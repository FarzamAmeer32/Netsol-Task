
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from netsol.app import app
from netsol.llm_service import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMUnavailableError,
    LLMResult,
)

client = TestClient(app)


def test_chat_success():
    fake_result = LLMResult(
        answer="Hello! How can I help?",
        model="gemini-2.5-flash",
        input_tokens=5,
        output_tokens=7,
    )

    with patch(
        "netsol.chat.generate_reply",
        new_callable=AsyncMock,
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Hello! How can I help?"
    assert data["model"] == "gemini-2.5-flash"
    assert data["usage"]["input_tokens"] == 5
    assert data["usage"]["output_tokens"] == 7


def test_chat_rejects_empty_message():
    response = client.post(
        "/api/v1/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_chat_rejects_oversized_message():
    response = client.post(
        "/api/v1/chat",
        json={"message": "a" * 4001},
    )

    assert response.status_code == 422


def test_chat_timeout_or_unavailable():
    with patch(
        "netsol.chat.generate_reply",
        new_callable=AsyncMock,
        side_effect=LLMUnavailableError(),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_chat_rate_limit():
    with patch(
        "netsol.chat.generate_reply",
        new_callable=AsyncMock,
        side_effect=LLMRateLimitError(),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 429


def test_chat_authentication_error():
    with patch(
        "netsol.chat.generate_reply",
        new_callable=AsyncMock,
        side_effect=LLMAuthenticationError(),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    # Your current chat.py maps this error to HTTP 503.
    assert response.status_code == 503
