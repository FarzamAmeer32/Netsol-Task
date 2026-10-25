# Task 03 — Connect the First LLM

A FastAPI application that connects a chatbot endpoint to Google's Gemini API using the official `google-genai` Python SDK.

This task introduces direct LLM API integration before using LangChain or LangGraph.

## Features

- `POST /api/v1/chat` endpoint for AI-generated responses.
- Separate asynchronous `generate_reply()` service.
- Environment-based configuration for the API key, model, timeout, and output-token limit.
- Pydantic request and response models.
- Input validation and whitespace trimming.
- Token usage reporting when available.
- Safe handling of provider authentication, rate-limit, and availability errors.
- Swagger UI documentation.

## Tech Stack

- Python 3.12+
- FastAPI
- Google Gen AI SDK (`google-genai`)
- Pydantic and Pydantic Settings
- Uvicorn
- uv
- Pytest and HTTPX for automated testing

## Project Structure

```text
src/
└── netsol/
    ├── app.py
    ├── chat.py
    ├── config.py
    └── llm_service.py

.env
.env.example
pyproject.toml
uv.lock
README.md
tests/
```

The structure above describes the intended files; adjust it to match the actual files in your repository.

## Setup

### 1. Install dependencies

```powershell
uv sync
```

If the dependencies have not yet been added:

```powershell
uv add google-genai pydantic-settings
uv add --dev pytest httpx
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_actual_api_key
LLM_MODEL=gemini-2.5-flash
LLM_TIMEOUT_SECONDS=30
LLM_MAX_OUTPUT_TOKENS=300
```

Replace the API key placeholder with your own key. Never commit `.env` or share your API key publicly.

The `.env.example` file should contain variable names and placeholder values only.

### 3. Run the application

If your FastAPI application instance is defined in `src/netsol/app.py`, run:

```powershell
uv run uvicorn netsol.app:app --reload --app-dir src
```

Open the following URLs:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Chat API

### POST `/api/v1/chat`

Generates an AI response for a supplied message.

Request:

```json
{
  "message": "Explain dependency injection in simple words."
}
```

Expected successful response (`200 OK`):

```json
{
  "answer": "Dependency injection provides an object with the dependencies it needs.",
  "model": "gemini-2.5-flash",
  "usage": {
    "input_tokens": 12,
    "output_tokens": 20
  }
}
```

The answer and token counts are illustrative, not a real API result. Actual token usage may be unavailable.

### Validation

- `message` must be a string.
- Empty or whitespace-only messages are rejected.
- Messages longer than 4,000 characters are rejected.
- Invalid input returns `422 Unprocessable Entity`.

### Error handling

| Status | Meaning |
|---|---|
| 422 | Invalid request data |
| 429 | Provider rate limit reached |
| 503 | Provider unavailable, timeout, or mapped provider authentication error |

Error responses should not expose API keys, raw provider responses, stack traces, or internal exception messages.

## Configuration

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Authenticates requests to Gemini |
| `LLM_MODEL` | Selects the Gemini model |
| `LLM_TIMEOUT_SECONDS` | Sets the provider request timeout |
| `LLM_MAX_OUTPUT_TOKENS` | Limits generated output size |

## Token Usage and Cost Considerations

- **Input tokens:** Tokens used to process the submitted prompt and any other input sent to the model.
- **Output tokens:** Tokens generated in the response.
- **Timeout:** Limits how long the application waits for the provider request.
- **Cost:** Depends on the selected model, token usage, and the provider's current pricing and free-tier limits.

Check the provider's current pricing and quota information before relying on a model for production workloads.

## Testing

Run the automated tests with:

```powershell
uv run pytest -v
```

Automated tests should use a mocked LLM service and must not make real paid API calls.

The test suite should cover successful generation, empty input, oversized input, provider timeout, authentication failure, and rate limiting.

## Current Development Status

The chat endpoint and Gemini service have been implemented. During local verification, the chat endpoint returned `503 Service Unavailable`. The underlying provider error has not yet been confirmed, so a successful real Gemini response remains unverified.

Automated test coverage and the complete acceptance criteria must be verified before considering Task 03 complete.

## Scope

This task uses the provider's official Python SDK directly.

**LangChain and LangGraph have not been introduced.**

Conversation history, database persistence, and workflow orchestration are outside the scope of this task.
