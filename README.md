# Netsol API

A backend API built with **FastAPI, PostgreSQL, SQLAlchemy, and LangGraph**. The project provides user authentication, JWT-based authorization, user-owned chat threads, persistent conversation history, and an AI-powered chat workflow.

## Features

- RESTful API built with FastAPI
- User registration and login
- JWT-based bearer authentication
- Protected user endpoints
- PostgreSQL database integration
- Asynchronous SQLAlchemy 2.x
- Database migrations using Alembic
- User-owned chat thread management
- Create, list, archive, and restore chat threads
- Persistent user and assistant messages
- Conversation history with pagination
- Google Gemini integration through a provider-independent LLM service
- LangGraph-based response generation and validation workflow
- Dependency injection for services and graph execution
- Centralized application error handling
- Automated tests using pytest

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| PostgreSQL | Relational database |
| SQLAlchemy 2.x | Async ORM |
| Alembic | Database migrations |
| Pydantic | Request and response validation |
| JWT | Authentication |
| Google Gemini | LLM provider |
| LangGraph | AI workflow orchestration |
| pytest | Automated testing |
| uv | Python dependency management |

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
│       │       ├── auth.py
│       │       ├── chat.py
│       │       ├── messages.py
│       │       ├── threads.py
│       │       ├── thread_messages.py
│       │       ├── users.py
│       │       └── router.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   └── exceptions.py
│       │
│       ├── db/
│       │   ├── models/
│       │   └── session.py
│       │
│       ├── graphs/
│       │   ├── __init__.py
│       │   ├── builder.py
│       │   ├── nodes.py
│       │   └── state.py
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

## Setup and Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Netsol
```

### 2. Install dependencies

Install `uv` if it is not already installed, then run:

```bash
uv sync --frozen
```

### 3. Configure environment variables

Create a `.env` file using `.env.example` as a template.

Configure the required database connection, JWT settings, and Gemini API key.

Do not commit your actual `.env` file or expose API keys.

### 4. Configure PostgreSQL

Make sure PostgreSQL is running and the database specified in your environment configuration exists.

### 5. Run database migrations

```bash
uv run alembic upgrade head
```

### 6. Start the development server

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

## API Overview

The API provides the following functionality:

| Area | Functionality |
|---|---|
| Health | Application health check |
| Authentication | User registration and login |
| Users | Retrieve authenticated user information |
| Messages | Basic message CRUD operations |
| Chat | AI-powered chat endpoint |
| Threads | Create, list, archive, and restore chat threads |
| Thread Messages | Send messages and retrieve conversation history |

### Thread and Conversation Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/threads` | Create a chat thread |
| GET | `/api/v1/threads` | List the authenticated user's threads |
| PATCH | `/api/v1/threads/{thread_id}` | Update or restore a thread |
| DELETE | `/api/v1/threads/{thread_id}` | Archive a thread |
| POST | `/api/v1/threads/{thread_id}/messages` | Send a message and receive an AI response |
| GET | `/api/v1/threads/{thread_id}/messages` | Retrieve conversation history |

Protected endpoints require a valid JWT bearer token.

## LangGraph Chat Workflow

Task 10 introduces LangGraph to organize AI response generation into a small, explicit workflow.

The workflow contains two nodes:

1. **generate_response:** Builds the prompt and calls the existing provider-independent `LLMService`.
2. **validate_response:** Checks that the generated answer contains visible text, normalizes whitespace, and enforces the configured maximum response length.

### Workflow Diagram

```mermaid
flowchart TD
    A([START]) --> B[generate_response]
    B --> C[validate_response]
    C --> D([END])
```

### Graph State

The graph receives a typed state containing:

- `user_message`
- `answer`
- `model`
- `input_tokens`
- `output_tokens`

The generated answer and usage information are returned through the graph state.

### Graph Lifecycle

The graph is built and compiled once during FastAPI application startup. The compiled graph is stored in application state and accessed through dependency injection.

The conversation service invokes the graph asynchronously using `ainvoke()`.

### Responsibilities Outside the Graph

The graph is responsible only for AI response generation and validation.

The following responsibilities remain outside the graph:

- Authentication and authorization
- Chat thread ownership checks
- Archived thread validation
- Database operations
- Message persistence
- Conversation history retrieval
- HTTP request and response handling

This separation keeps the AI workflow independent of the database and API layer.

## Conversation Persistence

When a user sends a message:

1. The API authenticates the user.
2. The conversation service verifies thread ownership and archive status.
3. LangGraph generates and validates the AI response.
4. The user message and assistant response are persisted together.
5. The thread's update timestamp is refreshed.

Both messages are saved within a database transaction. If generation or validation fails, no conversation messages are persisted.

Conversation history is stored in PostgreSQL and retrieved with pagination.

## Error Handling

The application handles common failures, including:

- Invalid request data
- Authentication and authorization failures
- Missing or inaccessible threads
- Archived thread message submissions
- LLM provider unavailability
- LLM rate limiting
- Invalid AI responses
- Database operation failures

AI provider failures are handled through application-level exceptions rather than exposing provider-specific errors to API clients.

## Running Tests

Run the complete test suite:

```bash
uv run pytest -v
```

The tests cover API functionality, authentication, authorization, thread management, conversation persistence, pagination, error handling, and LangGraph workflow behavior.

The LangGraph tests use a fake LLM service, avoiding real external API calls.

## Configuration

Application settings are managed through the configuration module and environment variables.

Important configuration includes:

- Database connection settings
- JWT authentication settings
- Gemini API key
- LLM model
- LLM request timeout
- Maximum input characters
- Maximum output tokens
- Maximum output characters

## Development Scope

The project is developed incrementally, with each task introducing a specific backend capability.

Task 10 introduces LangGraph because the application now has a structured AI workflow that benefits from explicit nodes, state management, and workflow orchestration.

LangGraph is currently used for a simple linear workflow. The implementation intentionally does not include checkpointers, conversational memory, RAG, tools, conditional routing, or human-in-the-loop execution.

## Future Improvements

- LangGraph checkpointing and conversation memory
- More advanced AI workflows
- Retrieval-Augmented Generation (RAG)
- Additional LLM providers
- Improved observability and logging
- Production deployment and containerization

---

**Project:** Netsol API  
**Framework:** FastAPI  
**Database:** PostgreSQL  
**AI Workflow:** LangGraph  
**LLM Provider:** Google Gemini
