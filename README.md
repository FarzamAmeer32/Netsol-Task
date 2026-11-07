# Python API Starter

A basic FastAPI project using Python and uv.

## Requirements

- Python 3.12+
- uv

## Local Setup

Install dependencies:

uv sync

Run the API:

uv run uvicorn netsol.app:app \
    --reload --app-dir src

## Docker Setup

Build and start:

docker compose up --build

Stop:

docker compose down

## Endpoints

GET /health