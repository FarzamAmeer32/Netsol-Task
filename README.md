# Netsol API — Task 04: Application Architecture

A modular FastAPI backend that separates API routes, request schemas, application configuration, error handling, and LLM service logic.

This task refactors the Task 03 chatbot into a maintainable architecture while preserving the health check and in-memory messages API.

## Features

- **Health check:** Verify that the API is responding.
- **Messages API:** Create, list, retrieve, update, and delete messages using in-memory storage.
- **Chat API:** Generate AI responses through the Gemini provider.
- **Dependency injection:** Keep the chat endpoint independent of the concrete LLM implementation.
- **Configuration management:** Load and validate environment-based settings.
- **Standardized error responses:** Return consistent JSON error structures.
- **Request IDs:** Accept valid `X-Request-ID` headers or generate IDs for request tracing.
- **Automated tests:** Test routes and error handling without making real Gemini API calls.

## Project Structure

```text
.
├── src/
│   └── netsol/
│       ├── __init__.py
│       ├── app.py
│       ├── api/
│       │   ├── dependencies.py
│       │   └── v1/
│       │       ├── router.py
│       │       ├── health.py
│       │       ├── messages.py
│       │       └── chat.py
│       ├── core/
│       │   ├── config.py
│       │   └── exceptions.py
│       ├── schemas/
│       │   └── chat.py
│       └── services/
│           └── llm.py
├── tests/
│   ├── test_messages.py
│   └── test_chat.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

The structure above describes the intended layout. Keep any additional files already required by your project.

## Architecture and Responsibilities

| Component | Responsibility |
|---|---|
| `app.py` | Creates the FastAPI application, configures lifespan, middleware, and exception handlers, and registers routers. |
| `api/v1/router.py` | Combines the versioned messages and chat routers. |
| `api/v1/health.py` | Provides the health-check endpoint. |
| `api/v1/messages.py` | Implements message CRUD operations using in-memory storage. |
| `api/v1/chat.py` | Validates chat requests and invokes the injected LLM service. |
| `api/dependencies.py` | Provides the LLM service through FastAPI dependency injection. |
| `schemas/chat.py` | Defines chat request, response, usage, and error models. |
| `services/llm.py` | Defines the LLM service interface and Gemini implementation. |
| `core/config.py` | Loads and validates environment-based settings. |
| `core/exceptions.py` | Defines application-specific LLM exceptions. |
| `tests/` | Contains automated tests for API behavior and error handling. |

## Setup

### Requirements

- Python 3.12 or later
- `uv`
- A Gemini API key for live chat requests

### 1. Install dependencies

From the project root:

```bash
uv sync
```

If the test dependencies have not yet been added:

```bash
uv add --dev pytest httpx
```

### 2. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

Example:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-2.5-flash
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=300
```

Use your actual API key in your local `.env` file. Do not commit `.env` or expose API keys in source code, logs, or screenshots.

The settings names must match those defined in `core/config.py`.

### 3. Run the application

```bash
uv run uvicorn netsol.app:app --reload --app-dir src
```

The API will be available at:

- Base URL: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Returns the API health status |
| GET | `/` | Returns basic service information |

Example response from `GET /health`:

```json
{
  "status": "ok"
}
```

### Messages

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/messages` | Create a message |
| GET | `/api/v1/messages` | List messages |
| GET | `/api/v1/messages/{message_id}` | Retrieve a message |
| PATCH | `/api/v1/messages/{message_id}` | Update message content |
| DELETE | `/api/v1/messages/{message_id}` | Delete a message |

Create a message:

```http
POST /api/v1/messages
Content-Type: application/json
```

```json
{
  "role": "user",
  "content": "Hello"
}
```

The messages API uses temporary in-memory storage. Messages are lost when the application restarts. No database is introduced in this task.

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/chat` | Generate an AI response |

Example request:

```http
POST /api/v1/chat
Content-Type: application/json
X-Request-ID: chat-test-123
```

```json
{
  "message": "Explain REST APIs in simple words."
}
```

Example success response:

```json
{
  "answer": "A REST API allows applications to communicate using HTTP.",
  "model": "gemini-2.5-flash",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 15
  }
}
```

The answer and token usage depend on the actual provider response.

## Error Handling

The application maps known exceptions to safe, consistent error responses.

| HTTP status | Error code | Meaning |
|---|---|---|
| 404 | `not_found` | The requested message does not exist. |
| 422 | `validation_error` | The request data is invalid. |
| 429 | `llm_rate_limited` | The LLM provider is rate-limiting requests. |
| 503 | `llm_unavailable` | The LLM provider is unavailable. |
| 503 | `llm_configuration_error` | The LLM provider configuration is invalid. |

Example error response:

```json
{
  "error": {
    "code": "llm_unavailable",
    "message": "The chatbot service is temporarily unavailable.",
    "request_id": "chat-test-123"
  }
}
```

The `X-Request-ID` response header allows a request to be correlated with server-side logs. Unexpected errors should be logged internally without exposing sensitive details to API clients.

## Dependency Injection and Testing

The chat endpoint depends on the `LLMService` interface rather than directly creating a Gemini client inside the route.

FastAPI dependency injection provides the service. Tests can replace that dependency using `app.dependency_overrides` and supply a fake implementation.

This allows tests to verify:

- Successful chat responses.
- Request validation.
- LLM provider failures.
- Rate-limit and configuration errors.
- Request ID behavior.

The tests do not need a real Gemini API call when the LLM dependency is overridden.

Run the test suite:

```bash
uv run pytest -v
```

Run individual test files:

```bash
uv run pytest tests/test_messages.py -v
uv run pytest tests/test_chat.py -v
```

## Scope of Task 04

This task focuses on application architecture and maintainability.

It does not introduce:

- PostgreSQL or another database.
- Authentication or authorization.
- LangChain or LangGraph.
- New chatbot functionality beyond the existing LLM integration.

The goal is to make the existing API easier to maintain, test, and extend in later tasks.