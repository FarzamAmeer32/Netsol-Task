# Netsol API

A backend API built with **FastAPI, Python, and PostgreSQL**. The project provides health monitoring, message management, LLM-powered chat, and secure user registration, with asynchronous database integration using SQLAlchemy 2.x.

## Features

- FastAPI application with modular project structure.
- PostgreSQL database integration.
- Asynchronous SQLAlchemy 2.x sessions.
- Database dependency injection.
- Alembic database migrations.
- User model with unique email constraint.
- Secure user registration with email and password validation.
- Argon2id password hashing.
- Duplicate email detection and conflict handling.
- Safe database error responses.
- Health and database readiness endpoints.
- Message CRUD operations.
- Gemini-powered chat integration.
- Automated tests using pytest.
- Docker Compose configuration for local development.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | API framework |
| PostgreSQL | Relational database |
| SQLAlchemy 2.x | ORM and async database access |
| Alembic | Database migrations |
| Pydantic Settings | Environment configuration |
| pwdlib with Argon2 | Password hashing |
| email-validator | Email validation |
| Gemini API | LLM integration |
| pytest | Automated testing |
| Docker Compose | Local services |

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
│       │       ├── health.py
│       │       └── ...
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── exceptions.py
│       │   └── security.py
│       │
│       ├── db/
│       │   ├── base.py
│       │   ├── session.py
│       │   └── models/
│       │       └── user.py
│       │
│       ├── repositories/
│       │   └── user.py
│       │
│       ├── schemas/
│       │   └── user.py
│       │
│       ├── services/
│       │   └── user.py
│       │
│       ├── app.py
│       └── ...
│
├── test/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_db_session.py
│   ├── test_user_model.py
│   └── test_transactions.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Prerequisites

Make sure you have:

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 16 (or Docker Desktop with Docker Compose)
- A Gemini API key for LLM-powered chat

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Netsol
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

Example:

```env
APP_NAME=Netsol API
APP_VERSION=0.5.0

GEMINI_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-2.5-flash
LLM_TIMEOUT_SECONDS=30
LLM_MAX_INPUT_CHARS=4000
LLM_MAX_OUTPUT_TOKENS=300

POSTGRES_DB=chatbot
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=your-local-password

DATABASE_URL=postgresql+asyncpg://chatbot_user:your-local-password@localhost:5432/chatbot
```

Use your actual local database credentials. Never commit your `.env` file or API keys.

## Database Setup

### Option 1: Using Docker Compose

Start the database service:

```bash
docker compose up -d db
```

### Option 2: Using a local PostgreSQL installation

Create a PostgreSQL database and configure the connection string in your `.env` file.

### Run database migrations

After starting PostgreSQL, apply migrations:

```bash
uv run alembic upgrade head
```

Check the current migration:

```bash
uv run alembic current
```

## Run the Application

Start the development server:

```bash
uv run uvicorn netsol.app:app --reload --app-dir src
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### API Documentation

FastAPI automatically provides interactive API documentation:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc