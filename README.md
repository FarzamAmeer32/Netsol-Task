# Python API Starter — Task 02

A simple REST API built with **FastAPI** to create, retrieve, list, update, and delete chat messages. This project builds on Task 01 and introduces request validation, HTTP status codes, query parameters, automated testing, and API documentation.

## Features

- Create messages with a role and content.
- List messages with pagination and optional role filtering.
- Retrieve a message by its ID.
- Update message content.
- Delete a message.
- Validate request bodies and query parameters using Pydantic and FastAPI.
- Return appropriate HTTP status codes and error responses.
- Explore endpoints through automatically generated Swagger documentation.
- Store messages in memory using a Python list.

## Tech Stack

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic
- uv
- Pytest
- HTTPX

## Project Structure

```text
Netsol/
├── src/
│   └── netsol/
│       ├── __init__.py
│       └── main.py
├── tests/
│   └── test_messages.py
├── .env.example
├── .gitignore
├── .python-version
├── .dockerignore
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── uv.lock
└── README.md
```

## Setup

### 1. Install dependencies

Make sure Python 3.12+ and `uv` are installed.

```powershell
uv sync
uv add --dev pytest httpx
```

### 2. Run the application

```powershell
uv run uvicorn python_api_starter.main:app --reload --app-dir src
```

The API will run locally at:

- **Base URL:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health

## API Endpoints

All message endpoints use the `/api/v1` prefix.

| Method