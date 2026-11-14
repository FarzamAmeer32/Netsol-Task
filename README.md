# Netsol API

A backend API built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. The project provides authentication, user management, chat functionality, and user-owned chat thread management.

## Features

- RESTful API built with FastAPI
- User registration and login
- JWT-based bearer authentication
- Protected user endpoints
- PostgreSQL database integration
- Asynchronous SQLAlchemy 2.x
- Database migrations using Alembic
- Chat message management
- User-owned chat threads
- Thread archiving and restoration
- Thread listing with filtering and pagination
- Centralized exception handling
- Request ID middleware
- Automated testing with pytest

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12+ | Programming language |
| FastAPI | Backend framework |
| PostgreSQL | Relational database |
| SQLAlchemy 2.x | ORM |
| Alembic | Database migrations |
| Pydantic | Request and response validation |
| JWT | Authentication |
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
│       │       └── threads.py
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
│       │
│       ├── repositories/
│       ├── schemas/
│       ├── services/
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
- Gemini API key, if using the LLM functionality

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

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

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

| Method | Endpoint | Description |
|---|---|---|
| GET | `/messages` | List messages |
| POST | `/messages` | Create a message |
| GET | `/messages/{message_id}` | Retrieve a message |
| PATCH | `/messages/{message_id}` | Update a message |
| DELETE | `/messages/{message_id}` | Delete a message |

### Chat Threads

All thread endpoints require bearer authentication.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/threads` | Create a chat thread |
| GET | `/threads` | List the authenticated user's threads |
| GET | `/threads/{thread_id}` | Retrieve an owned thread |
| PATCH | `/threads/{thread_id}` | Update title or archive status |
| DELETE | `/threads/{thread_id}` | Permanently delete a thread |

### Thread Functionality

**Create a thread**

```json
{
  "title": "My AI Project"
}
```

The authenticated user's ID is automatically assigned as the thread owner.

**List threads**

```text
GET /api/v1/threads?limit=20&offset=0
```

Optional filtering:

```text
GET /api/v1/threads?is_archived=true
```

Supported query parameters:

- `limit`: Number of records to return (1–100, default 20).
- `offset`: Number of records to skip (default 0).
- `is_archived`: Filter by archive status.

The response includes the matching items, total count, limit, and offset.

**Update a thread**

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

Only the title and archive status can be updated.

**Delete a thread**

```text
DELETE /api/v1/threads/{thread_id}
```

Returns HTTP `204 No Content` on successful deletion.

### Thread Ownership and Security

- All thread endpoints require an authenticated user.
- A thread's owner is determined from the authenticated user, not from client-provided data.
- Users can only retrieve, update, list, or delete their own threads.
- Accessing another user's thread returns the same `404` response as accessing a nonexistent thread.
- Deleting a user cascades to their owned threads through the database foreign key.

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

Tests use a dedicated test database configured through `TEST_DATABASE_URL` or the project's test database configuration.

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

## Development Notes

- Use dependency injection for database sessions and authentication.
- Keep API routes, services, repositories, and schemas separated.
- Keep database operations asynchronous.
- Use Alembic for schema changes.
- Never expose passwords, secret keys, or JWT secrets.
- Keep user-owned resources protected by owner-scoped database queries.

## License

Add your project's license information here.
