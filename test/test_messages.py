
import os

# Required because app startup validates the Gemini configuration.
os.environ.setdefault("GEMINI_API_KEY", "test-key")

from fastapi.testclient import TestClient

from netsol.app import app
from netsol.api.v1 import messages as messages_module


def setup_function():
    # Keep each test independent.
    messages_module.messages.clear()
    messages_module.next_message_id = 1


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_create_message():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/messages",
            json={"role": "user", "content": "Hello"},
        )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["role"] == "user"
    assert data["content"] == "Hello"
    assert "created_at" in data


def test_list_messages():
    with TestClient(app) as client:
        client.post(
            "/api/v1/messages",
            json={"role": "user", "content": "Hello"},
        )
        client.post(
            "/api/v1/messages",
            json={"role": "assistant", "content": "Hi there"},
        )

        response = client.get("/api/v1/messages")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_messages_filters_by_role():
    with TestClient(app) as client:
        client.post(
            "/api/v1/messages",
            json={"role": "user", "content": "Hello"},
        )
        client.post(
            "/api/v1/messages",
            json={"role": "assistant", "content": "Hi"},
        )

        response = client.get(
            "/api/v1/messages",
            params={"role": "user"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "user"


def test_list_messages_pagination():
    with TestClient(app) as client:
        for content in ["First", "Second", "Third"]:
            client.post(
                "/api/v1/messages",
                json={"role": "user", "content": content},
            )

        response = client.get(
            "/api/v1/messages",
            params={"limit": 1, "offset": 0},
        )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["content"] == "Third"


def test_get_message():
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/messages",
            json={"role": "user", "content": "Hello"},
        )
        message_id = created.json()["id"]

        response = client.get(f"/api/v1/messages/{message_id}")

    assert response.status_code == 200
    assert response.json()["content"] == "Hello"


def test_update_message():
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/messages",
            json={"role": "user", "content": "Old text"},
        )
        message_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/messages/{message_id}",
            json={"content": "Updated text"},
        )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated text"


def test_delete_message():
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/messages",
            json={"role": "user", "content": "Delete me"},
        )
        message_id = created.json()["id"]

        response = client.delete(f"/api/v1/messages/{message_id}")
        get_response = client.get(f"/api/v1/messages/{message_id}")

    assert response.status_code == 204
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "not_found"


def test_missing_message_returns_standard_error():
    with TestClient(app) as client:
        response = client.get("/api/v1/messages/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"]
    assert response.headers["X-Request-ID"]


def test_invalid_message_returns_validation_error():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/messages",
            json={"role": "invalid-role", "content": "Hello"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["request_id"]


def test_empty_message_content_is_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/messages",
            json={"role": "user", "content": "   "},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_request_id_is_preserved():
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"X-Request-ID": "test-request-123"},
        )

    assert response.headers["X-Request-ID"] == "test-request-123"
