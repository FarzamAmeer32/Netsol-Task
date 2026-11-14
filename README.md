# Netsol API

A backend API built with **FastAPI, PostgreSQL, and SQLAlchemy 2.x**. The project provides authentication, user management, LLM-powered chat functionality, user-owned chat threads, and persistent conversation history.

## Features

- RESTful API built with FastAPI
- User registration and login
- JWT-based Bearer authentication
- Protected user endpoints
- PostgreSQL database integration
- Asynchronous SQLAlchemy 2.x
- Database migrations using Alembic
- Gemini LLM integration
- Chat message management
- User-owned chat threads
- Thread archiving and restoration
- Thread listing with filtering and pagination
- Persistent conversation messages
- User and assistant message persistence
- Sequential message ordering per thread
- Cursor-based conversation history pagination
- Thread ownership and resource-level authorization
- Atomic persistence of user and assistant messages
- Database cascade deletion
- Centralized exception handling
- Request ID middleware
- Automated testing with pytest

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12+ | Programming language |
| FastAPI | Backend framework |
| PostgreSQL | Relational database |
| SQLAlchemy 2.x | ORM and async database operations |
| Alembic | Database migrations |
| Pydantic | Request and response validation |
| JWT | Authentication |
| Google Gemini | LLM integration |
| uv | Dependency and project management |
| pytest | Automated testing |

## Project Structure

```text
Netsol/
│
├── alembic/
│   └── versions/
│
├── src/
│   └── netsol/
│       ├── api/
│       │   ├── dependencies.py
│       │   └── v1/
│       │       ├── router.py
│       │       ├── auth.py
│       │       ├── users.py
│       │       ├── messages.py
│       │       ├── threads.py
│       │       ├── thread_messages.py
│       │       └── chat.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   └── exceptions.py
│       │
│       ├── db/
│       │   ├── base.py
│       │   ├── session.py
│       │   └── models/
│       │       ├── user.py
│       │       ├── thread.py
│       │       └── message.py
│       │
│       ├── repositories/
│       ├── schemas/
│       ├── services/
│       │   ├── llm.py
│       │   ├── thread.py
│       │   └── conversation.py
│       │
│       └── app.py
│
├── test/
├── .env.example
├── alembic.ini
├── pyproject.toml
├── uv.lock
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Netsol
```

### 2. Install dependencies

Install uv if it is not already installed.

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file using `.env.example`.

Configure the required values, including:

- Database connection URL
- JWT authentication settings
- Gemini API key

Do not commit your `.env` file or expose API keys.

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

### 5. Start the development server

```bash
uv run uvicorn netsol.app:app --reload --app-dir src
```

The API will be available at:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

## API Endpoints

All API endpoints are available under `/api/v1`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Authenticate a user |

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/me` | Get authenticated user profile |

### Messages

These endpoints provide the original message CRUD functionality.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/messages` | List messages |
| POST | `/messages` | Create a message |
| GET | `/messages/{message_id}` | Retrieve a message |
| PATCH | `/messages/{message_id}` | Update a message |
| DELETE | `/messages/{message_id}` | Delete a message |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Generate an AI response |

### Chat Threads

All thread endpoints require Bearer authentication.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/threads` | Create a chat thread |
| GET | `/threads` | List authenticated user's threads |
| GET | `/threads/{thread_id}` | Retrieve an owned thread |
| PATCH | `/threads/{thread_id}` | Update title or archive status |
| DELETE | `/threads/{thread_id}` | Permanently delete a thread |

### Persistent Conversation Messages

These endpoints manage messages associated with individual chat threads.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/threads/{thread_id}/messages` | Send a message and generate an AI reply |
| GET | `/threads/{thread_id}/messages` | Retrieve conversation history |

## Chat Thread Functionality

### Create a thread

```http
POST /api/v1/threads
```

Request:

```json
{
  "title": "My AI Project"
}
```

The authenticated user's ID is automatically assigned as the thread owner.

### List threads

```http
GET /api/v1/threads?limit=20&offset=0
```

Optional filtering:

```http
GET /api/v1/threads?is_archived=true
```

Supported query parameters:

- `limit`: Number of records to return (1–100, default 20).
- `offset`: Number of records to skip (default 0).
- `is_archived`: Filter by archive status.

### Update a thread

Update the title:

```json
{
  "title": "Updated Project Title"
}
```

Archive a thread:

```json
{
  "is_archived": true
}
```

Restore an archived thread:

```json
{
  "is_archived": false
}
```

### Delete a thread

```http
DELETE /api/v1/threads/{thread_id}
```

Returns HTTP `204 No Content` on successful deletion.

## Persistent Conversation History

Task 09 introduces persistent chat messages associated with user-owned threads.

Each message contains:

- Unique UUID
- Thread ID
- Role (`user` or `assistant`)
- Message content
- Sequence number
- Optional LLM model information
- Optional input and output token counts
- Creation timestamp

### Send a message

```http
POST /api/v1/threads/{thread_id}/messages
```

Request:

```json
{
  "content": "Explain machine learning."
}
```

The API:

1. Authenticates the user.
2. Verifies thread ownership and archive status.
3. Sends the current message to the injected LLM service.
4. Persists the user message and assistant response.
5. Updates the thread's timestamp.
6. Returns both persisted messages.

Example response:

```json
{
  "user_message": {
    "id": "user-message-uuid",
    "role": "user",
    "content": "Explain machine learning.",
    "sequence": 1
  },
  "assistant_message": {
    "id": "assistant-message-uuid",
    "role": "assistant",
    "content": "Machine learning is a branch of AI...",
    "sequence": 2,
    "model": "gemini-2.5-flash",
    "input_tokens": 10,
    "output_tokens": 25
  }
}
```

The UUIDs and token counts above are illustrative.

### Retrieve conversation history

```http
GET /api/v1/threads/{thread_id}/messages
```

The endpoint returns messages in ascending sequence order.

### Cursor-based pagination

```http
GET /api/v1/threads/{thread_id}/messages?limit=50
```

Retrieve the next page using the returned cursor:

```http
GET /api/v1/threads/{thread_id}/messages?limit=50&after=50
```

Supported query parameters:

- `limit`: Number of messages returned (1–100, default 50).
- `after`: Return messages with sequence numbers greater than the supplied cursor.

The response includes:

- `items`: Retrieved messages.
- `limit`: Requested page size.
- `next_cursor`: Cursor for the next page, when more results exist.
- `has_more`: Indicates whether additional messages exist.

### Message ordering

Messages use sequential numbering within each thread.

For example:

| Sequence | Role | Content |
|---|---|---|
| 1 | user | Hello |
| 2 | assistant | Hello! How can I help? |
| 3 | user | Explain Python |
| 4 | assistant | Python is a programming language... |

A unique database constraint on `(thread_id, sequence)` prevents duplicate sequence numbers within a thread.

### Transaction and persistence behavior

- The LLM is called before starting the database write transaction.
- User and assistant messages are persisted together.
- Both messages receive consecutive sequence numbers.
- The thread's `updated_at` timestamp is updated in the same transaction.
- If database persistence fails, the transaction is rolled back.
- If LLM generation fails, no messages are persisted.
- A database-level cascade deletes messages when their parent thread is deleted.

### Archived threads

- Archived threads remain readable.
- New messages cannot be sent to archived threads.
- Attempting to send a message to an archived thread returns HTTP `409 Conflict`.

## Thread Ownership and Security

- All thread and conversation endpoints require authenticated users.
- Thread ownership is determined from the authenticated user.
- Clients cannot assign their own owner IDs.
- Users can only access their own threads and conversation history.
- Accessing another user's thread returns `404 Not Found`.
- Deleting a user cascades to their owned threads.
- Deleting a thread cascades to its associated messages.

## Database Migrations

Alembic manages database schema changes.

Generate a migration:

```bash
uv run alembic revision --autogenerate -m "migration_description"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Check the current migration:

```bash
uv run alembic current
```

Rollback one migration:

```bash
uv run alembic downgrade -1
```

## Testing

Run the complete test suite:

```bash
uv run pytest -q
```

Run a specific test file:

```bash
uv run pytest test/test_auth.py -q
```

Run thread tests:

```bash
uv run pytest test/test_threads.py -q
```

Run conversation message tests:

```bash
uv run pytest test/test_thread_messages.py -q
```

Tests use a dedicated test database configured through `TEST_DATABASE_URL` or the project's test database configuration.

LLM services are mocked during tests to avoid external API calls.

## Error Handling

The API uses centralized exception handling with a consistent error response structure.

Example:

```json
{
  "error": {
    "code": "thread_not_found",
    "message": "Chat thread was not found.",
    "request_id": "request-uuid"
  }
}
```

Common conversation errors include:

| HTTP Status | Error | Description |
|---|---|---|
| 401 | `unauthorized` | Authentication required |
| 404 | `thread_not_found` | Thread not found or not owned by user |
| 409 | `thread_archived` | Cannot send messages to archived thread |
| 422 | `validation_error` | Invalid request data |
| 429 | `llm_rate_limited` | LLM rate limit reached |
| 503 | `llm_unavailable` | LLM service unavailable |
| 500 | `conversation_error` | Conversation operation failed |

## Development Notes

- Use dependency injection for database sessions, authentication, and LLM services.
- Keep API routes, services, repositories, and schemas separated.
- Keep database operations asynchronous.
- Use Alembic for schema changes.
- Use owner-scoped queries for user-owned resources.
- Never expose passwords, API keys, or JWT secrets.
- Use database transactions for operations that must succeed or fail together.


