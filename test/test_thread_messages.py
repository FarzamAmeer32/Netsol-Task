
import uuid

import pytest

from netsol.app import app
from netsol.api.dependencies import get_llm_service
from netsol.services.llm import LLMResult
from netsol.core.exceptions import (
    LLMRateLimitError,
    LLMUnavailableError,
)
from sqlalchemy.exc import SQLAlchemyError
import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.db.models.message import ChatMessage

import netsol.services.conversation as conversation_service

class FakeLLMService:
    def __init__(self, error=None):
        self.error = error

    async def generate_reply(self, message: str) -> LLMResult:
        if self.error:
            raise self.error

        return LLMResult(
            answer=f"Test reply to: {message}",
            model="fake-model",
            input_tokens=5,
            output_tokens=10,
        )


@pytest.fixture
def fake_llm():
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService()
    )

    yield

    app.dependency_overrides.pop(get_llm_service, None)


def create_authenticated_user(auth_client):
    email = f"{uuid.uuid4()}@example.com"
    password = "MyStrongPass!2026"

    auth_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_send_message_success(auth_client, fake_llm):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Test Conversation"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    response = auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello AI"},
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    user_message = data["user_message"]
    assistant_message = data["assistant_message"]

    # User message
    assert user_message["role"] == "user"
    assert user_message["content"] == "Hello AI"
    assert user_message["sequence"] == 1

    # Assistant message
    assert assistant_message["role"] == "assistant"
    assert assistant_message["content"] == "Test reply to: Hello AI"
    assert assistant_message["sequence"] == 2

    # LLM metadata
    assert assistant_message["model"] == "fake-model"
    assert assistant_message["input_tokens"] == 5
    assert assistant_message["output_tokens"] == 10

    # Both messages belong to the same thread
    assert user_message["id"]
    assert assistant_message["id"]


def test_get_conversation_history(auth_client, fake_llm):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "History Test"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    # Send first message
    auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
        headers=headers,
    )

    # Send second message
    auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "How are you?"},
        headers=headers,
    )

    # Retrieve conversation history
    response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()
    messages = data["items"]

    assert len(messages) == 4

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]

    assert [message["sequence"] for message in messages] == [
        1, 2, 3, 4
    ]

    assert messages[0]["content"] == "Hello"
    assert messages[2]["content"] == "How are you?"

    assert data["has_more"] is False
    assert data["next_cursor"] is None

def test_get_conversation_history_pagination(auth_client, fake_llm):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Pagination Test"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    # Create 3 exchanges = 6 messages
    for content in ["First", "Second", "Third"]:
        auth_client.post(
            f"/api/v1/threads/{thread_id}/messages",
            json={"content": content},
            headers=headers,
        )

    # First page
    first_response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages?limit=2",
        headers=headers,
    )

    assert first_response.status_code == 200

    first_data = first_response.json()

    assert len(first_data["items"]) == 2
    assert first_data["items"][0]["sequence"] == 1
    assert first_data["items"][1]["sequence"] == 2
    assert first_data["has_more"] is True
    assert first_data["next_cursor"] == 2

    # Second page
    second_response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages?limit=2&after=2",
        headers=headers,
    )

    second_data = second_response.json()

    assert len(second_data["items"]) == 2
    assert second_data["items"][0]["sequence"] == 3
    assert second_data["items"][1]["sequence"] == 4
    assert second_data["has_more"] is True
    assert second_data["next_cursor"] == 4

    # Third page
    third_response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages?limit=2&after=4",
        headers=headers,
    )

    third_data = third_response.json()

    assert len(third_data["items"]) == 2
    assert third_data["items"][0]["sequence"] == 5
    assert third_data["items"][1]["sequence"] == 6
    assert third_data["has_more"] is False
    assert third_data["next_cursor"] is None

def test_user_cannot_access_another_users_messages(auth_client, fake_llm):
    owner_headers = create_authenticated_user(auth_client)
    other_headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Private Conversation"},
        headers=owner_headers,
    )

    thread_id = thread_response.json()["id"]

    response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "thread_not_found"

def test_cannot_send_message_to_archived_thread(auth_client, fake_llm):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Archived Conversation"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    # Archive the thread
    archive_response = auth_client.patch(
        f"/api/v1/threads/{thread_id}",
        json={"is_archived": True},
        headers=headers,
    )

    assert archive_response.status_code == 200

    # Attempt to send a message
    response = auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "thread_archived"

@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"content": ""},
        {"content": "    "},
        {"content": "x" * 4001},
        {"content": "\n\t"},
        {"content": "Hello", "role": "assistant"},
        {"content": "Hello", "sequence": 100},
        {"content": "Hello", "model": "fake-model"},
    ],
)
def test_send_message_rejects_invalid_input(
    auth_client, fake_llm, payload
):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Validation Test"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    response = auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"

@pytest.mark.parametrize(
    "llm_error, expected_status, expected_code",
    [
        (LLMUnavailableError(), 503, "llm_unavailable"),
        (LLMRateLimitError(), 429, "llm_rate_limited"),
    ],
)
def test_llm_failure_does_not_save_messages(
    auth_client,
    llm_error,
    expected_status,
    expected_code,
):
    app.dependency_overrides[get_llm_service] = (
        lambda: FakeLLMService(error=llm_error)
    )

    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "LLM Failure Test"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    response = auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
        headers=headers,
    )

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code

    # Verify no messages were saved
    history_response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages",
        headers=headers,
    )

    assert history_response.status_code == 200
    assert history_response.json()["items"] == []


def test_thread_messages_require_authentication(auth_client, fake_llm):
    thread_id = str(uuid.uuid4())

    post_response = auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
    )

    get_response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages",
    )

    assert post_response.status_code == 401
    assert get_response.status_code == 401


def test_get_messages_from_unknown_thread(auth_client, fake_llm):
    headers = create_authenticated_user(auth_client)

    response = auth_client.get(
        f"/api/v1/threads/{uuid.uuid4()}/messages",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "thread_not_found"


def test_user_cannot_send_message_to_another_users_thread(
    auth_client, fake_llm
):
    owner_headers = create_authenticated_user(auth_client)
    other_headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Private Thread"},
        headers=owner_headers,
    )

    thread_id = thread_response.json()["id"]

    response = auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "thread_not_found"

def test_empty_thread_returns_empty_history(auth_client, fake_llm):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Empty Conversation"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["has_more"] is False
    assert response.json()["next_cursor"] is None

def test_archived_thread_messages_are_readable(auth_client, fake_llm):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Archived History"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
        headers=headers,
    )

    auth_client.patch(
        f"/api/v1/threads/{thread_id}",
        json={"is_archived": True},
        headers=headers,
    )

    response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


@pytest.mark.parametrize(
    "query",
    [
        "?limit=0",
        "?limit=101",
        "?limit=-1",
        "?after=-1",
    ],
)
def test_message_history_rejects_invalid_pagination(
    auth_client, fake_llm, query
):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Pagination Validation"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages{query}",
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"    

def test_message_pair_rolls_back_if_second_insert_fails(
    auth_client, fake_llm, monkeypatch
):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Rollback Test"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    original_create = conversation_service.create_message_record
    call_count = 0

    async def failing_create_message(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise SQLAlchemyError("Simulated database failure")

        return await original_create(*args, **kwargs)

    monkeypatch.setattr(
        conversation_service,
        "create_message_record",
        failing_create_message,
    )

    response = auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
        headers=headers,
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "conversation_error"

    # The first insertion must also have been rolled back.
    history_response = auth_client.get(
        f"/api/v1/threads/{thread_id}/messages",
        headers=headers,
    )

    assert history_response.status_code == 200
    assert history_response.json()["items"] == []    

def test_deleting_thread_deletes_its_messages(
    auth_client, fake_llm, test_engine
):
    headers = create_authenticated_user(auth_client)

    thread_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Cascade Delete Test"},
        headers=headers,
    )

    thread_id = thread_response.json()["id"]

    auth_client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"content": "Hello"},
        headers=headers,
    )

    async def count_messages():
        async with AsyncSession(
            test_engine,
            expire_on_commit=False,
        ) as session:
            result = await session.execute(
                select(func.count()).select_from(ChatMessage).where(
                    ChatMessage.thread_id == uuid.UUID(thread_id)
                )
            )
            return result.scalar_one()

    assert asyncio.run(count_messages()) == 2

    delete_response = auth_client.delete(
        f"/api/v1/threads/{thread_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    assert asyncio.run(count_messages()) == 0    