
from fastapi.testclient import TestClient

from netsol.app import app, messages

client = TestClient(app)


def setup_function():
    # Reset in-memory data before each test.
    messages.clear()
    import netsol.app as main
    main.next_message_id = 1


def test_create_message():
    response = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "What is FastAPI?"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["role"] == "user"
    assert data["content"] == "What is FastAPI?"
    assert "created_at" in data


def test_reject_empty_message():
    response = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "   "},
    )

    assert response.status_code == 422


def test_list_messages_with_filters():
    client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Question one"},
    )
    client.post(
        "/api/v1/messages",
        json={"role": "assistant", "content": "Answer one"},
    )
    client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Question two"},
    )

    response = client.get(
        "/api/v1/messages",
        params={"limit": 1, "offset": 1, "role": "user"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Question two"


def test_retrieve_existing_message():
    created = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Hello"},
    ).json()

    response = client.get(f"/api/v1/messages/{created['id']}")

    assert response.status_code == 200
    assert response.json()["content"] == "Hello"


def test_missing_message_returns_404():
    response = client.get("/api/v1/messages/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Message with ID 999 not found."


def test_update_message():
    created = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Old content"},
    ).json()

    response = client.patch(
        f"/api/v1/messages/{created['id']}",
        json={"content": "New content"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "New content"


def test_delete_message():
    created = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Delete me"},
    ).json()
    message_id = created["id"]

    response = client.delete(f"/api/v1/messages/{message_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/v1/messages/{message_id}").status_code == 404


def test_invalid_query_parameters():
    response = client.get("/api/v1/messages", params={"limit": 101})

    assert response.status_code == 422
