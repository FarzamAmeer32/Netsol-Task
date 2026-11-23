import uuid


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

    return {
        "Authorization": f"Bearer {token}"
    }


def test_create_thread_success(auth_client):
    headers = create_authenticated_user(auth_client)

    response = auth_client.post(
        "/api/v1/threads",
        json={"title": "My AI Project"},
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "My AI Project"
    assert data["is_archived"] is False
    assert data["owner_id"]
    assert data["id"]


def test_create_thread_rejects_owner_id(auth_client):
    headers = create_authenticated_user(auth_client)

    response = auth_client.post(
        "/api/v1/threads",
        json={
            "title": "My AI Project",
            "owner_id": str(uuid.uuid4()),
        },
        headers=headers,
    )

    assert response.status_code == 422

def test_get_thread_success(auth_client):
    headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "My First Thread"},
        headers=headers,
    )

    thread_id = create_response.json()["id"]

    response = auth_client.get(
        f"/api/v1/threads/{thread_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == thread_id
    assert response.json()["title"] == "My First Thread"


def test_user_cannot_access_another_users_thread(auth_client):
    owner_headers = create_authenticated_user(auth_client)
    other_headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Private Thread"},
        headers=owner_headers,
    )

    thread_id = create_response.json()["id"]

    response = auth_client.get(
        f"/api/v1/threads/{thread_id}",
        headers=other_headers,
    )
    

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "thread_not_found"
    assert response.json()["error"]["message"] == "Chat thread was not found." 

def test_list_threads_success(auth_client):
    headers = create_authenticated_user(auth_client)

    for title in ["Thread 1", "Thread 2", "Thread 3"]:
        auth_client.post(
            "/api/v1/threads",
            json={"title": title},
            headers=headers,
        )

    response = auth_client.get(
        "/api/v1/threads",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 3
    assert data["total"] == 3
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_threads_only_returns_owners_threads(auth_client):
    owner_headers = create_authenticated_user(auth_client)
    other_headers = create_authenticated_user(auth_client)

    auth_client.post(
        "/api/v1/threads",
        json={"title": "Owner Thread"},
        headers=owner_headers,
    )

    auth_client.post(
        "/api/v1/threads",
        json={"title": "Other User Thread"},
        headers=other_headers,
    )

    response = auth_client.get(
        "/api/v1/threads",
        headers=owner_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Owner Thread"    

def test_list_threads_pagination(auth_client):
    headers = create_authenticated_user(auth_client)

    for title in ["Thread 1", "Thread 2", "Thread 3"]:
        auth_client.post(
            "/api/v1/threads",
            json={"title": title},
            headers=headers,
        )

    response = auth_client.get(
        "/api/v1/threads?limit=2&offset=1",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 1


def test_list_threads_archived_filter(auth_client):
    headers = create_authenticated_user(auth_client)

    first = auth_client.post(
        "/api/v1/threads",
        json={"title": "Active Thread"},
        headers=headers,
    )

    second = auth_client.post(
        "/api/v1/threads",
        json={"title": "Archived Thread"},
        headers=headers,
    )

    archived_id = second.json()["id"]

    auth_client.patch(
        f"/api/v1/threads/{archived_id}",
        json={"is_archived": True},
        headers=headers,
    )

    response = auth_client.get(
        "/api/v1/threads?is_archived=true",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == archived_id
    assert data["items"][0]["is_archived"] is True    

def test_update_thread_title(auth_client):
    headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Old Title"},
        headers=headers,
    )

    thread_id = create_response.json()["id"]

    response = auth_client.patch(
        f"/api/v1/threads/{thread_id}",
        json={"title": "New Title"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New Title"

def test_archive_and_restore_thread(auth_client):
    headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "My Thread"},
        headers=headers,
    )

    thread_id = create_response.json()["id"]

    archive_response = auth_client.patch(
        f"/api/v1/threads/{thread_id}",
        json={"is_archived": True},
        headers=headers,
    )

    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True

    restore_response = auth_client.patch(
        f"/api/v1/threads/{thread_id}",
        json={"is_archived": False},
        headers=headers,
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["is_archived"] is False
def test_update_thread_rejects_empty_body(auth_client):
    headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "My Thread"},
        headers=headers,
    )

    thread_id = create_response.json()["id"]

    response = auth_client.patch(
        f"/api/v1/threads/{thread_id}",
        json={},
        headers=headers,
    )

    assert response.status_code == 422

def test_update_thread_rejects_owner_id(auth_client):
    headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "My Thread"},
        headers=headers,
    )

    thread_id = create_response.json()["id"]

    response = auth_client.patch(
        f"/api/v1/threads/{thread_id}",
        json={"owner_id": str(uuid.uuid4())},
        headers=headers,
    )

    assert response.status_code == 422

def test_get_unknown_thread_returns_404(auth_client):
    headers = create_authenticated_user(auth_client)

    response = auth_client.get(
        f"/api/v1/threads/{uuid.uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "thread_not_found"
    assert response.json()["error"]["message"] == "Chat thread was not found."


def test_delete_thread_success(
    auth_client,
    fake_checkpointer,
):
    headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Thread To Delete"},
        headers=headers,
    )

    assert create_response.status_code == 201

    thread_id = create_response.json()["id"]

    owner_id = create_response.json()["owner_id"]

    delete_response = auth_client.delete(
        f"/api/v1/threads/{thread_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    # Verify that the corresponding LangGraph checkpoint was deleted.
    expected_graph_thread_id = f"chat:{owner_id}:{thread_id}"

    assert fake_checkpointer.deleted_thread_ids == [
        expected_graph_thread_id
    ]

    # Verify that the application thread was deleted too.
    get_response = auth_client.get(
        f"/api/v1/threads/{thread_id}",
        headers=headers,
    )

    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "thread_not_found"


def test_user_cannot_delete_another_users_thread(auth_client,fake_checkpointer):
    owner_headers = create_authenticated_user(auth_client)
    other_headers = create_authenticated_user(auth_client)

    create_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "Private Thread"},
        headers=owner_headers,
    )

    thread_id = create_response.json()["id"]

    response = auth_client.delete(
        f"/api/v1/threads/{thread_id}",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "thread_not_found"
    

    owner_response = auth_client.get(
        f"/api/v1/threads/{thread_id}",
        headers=owner_headers,
    )

    assert owner_response.status_code == 200
    assert fake_checkpointer.deleted_thread_ids == []

def test_threads_require_authentication(auth_client):
    responses = [
        auth_client.post(
            "/api/v1/threads",
            json={"title": "Unauthorized Thread"},
        ),
        auth_client.get("/api/v1/threads"),
        auth_client.get(f"/api/v1/threads/{uuid.uuid4()}"),
        auth_client.patch(
            f"/api/v1/threads/{uuid.uuid4()}",
            json={"title": "Updated"},
        ),
        auth_client.delete(f"/api/v1/threads/{uuid.uuid4()}"),
    ]

    for response in responses:
        assert response.status_code == 401

def test_create_thread_rejects_invalid_titles(auth_client):
    headers = create_authenticated_user(auth_client)

    empty_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "   "},
        headers=headers,
    )

    assert empty_response.status_code == 422

    long_response = auth_client.post(
        "/api/v1/threads",
        json={"title": "A" * 121},
        headers=headers,
    )

    assert long_response.status_code == 422                                        