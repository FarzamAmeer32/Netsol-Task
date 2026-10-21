
# Python API Starter

A reproducible FastAPI project using Python 3.12+, uv, Uvicorn, and Docker Compose.

## Requirements

- Python 3.12+ and uv for local development
- Docker Desktop with Docker Compose for containerized development
- Git

## Setup

Install project dependencies:

```powershell
uv sync --locked
```

## Run locally

```powershell
uv run uvicorn python_api_starter.main:app --reload --app-dir src
```

Health endpoint: http://127.0.0.1:8000/health

Interactive API documentation: http://127.0.0.1:8000/docs

## Run with Docker Compose

```powershell
docker compose up --build
```

Health endpoint: http://127.0.0.1:8000/health

Stop the containers with:

```powershell
docker compose down
```

## Configuration

See `.env.example` for the example application configuration.

## Project layout

- `src/python_api_starter/main.py`: FastAPI application and health endpoint
- `pyproject.toml`: project metadata and dependencies
- `uv.lock`: locked dependency versions
- `Dockerfile`: container image instructions
- `compose.yaml`: Docker Compose configuration
- `.gitignore`: excludes generated files and local secrets
- `.env.example`: example configuration

## Health endpoint

`GET /health` returns HTTP 200 with JSON containing the service status and version.
