
import re
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from netsol.api.v1.health import router as health_router
from netsol.api.v1.router import router as v1_router
from netsol.core.config import get_settings
from netsol.core.exceptions import (
    LLMConfigurationError,
    LLMRateLimitError,
    LLMUnavailableError,
)
from netsol.schemas.chat import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate environment configuration when the app starts.
    get_settings()
    yield


app = FastAPI(
    title="Netsol API",
    version="0.4.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    supplied_id = request.headers.get("X-Request-ID", "")

    if re.fullmatch(r"[A-Za-z0-9._:-]{1,64}", supplied_id):
        request_id = supplied_id
    else:
        request_id = str(uuid4())

    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:
        # Avoid exposing internal exception details to the client.
        response = error_response(
            request,
            500,
            "internal_server_error",
            "An unexpected error occurred.",
        )

    response.headers["X-Request-ID"] = request_id
    return response


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
):
    request_id = getattr(
        request.state, "request_id", str(uuid4())
    )

    body = ErrorResponse(
        error={
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    )

    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(
    request: Request, exc: LLMUnavailableError
):
    return error_response(
        request,
        503,
        "llm_unavailable",
        "The chatbot service is temporarily unavailable.",
    )


@app.exception_handler(LLMRateLimitError)
async def llm_rate_limit_handler(
    request: Request, exc: LLMRateLimitError
):
    return error_response(
        request,
        429,
        "llm_rate_limited",
        "Please try again later.",
    )


@app.exception_handler(LLMConfigurationError)
async def llm_configuration_handler(
    request: Request, exc: LLMConfigurationError
):
    return error_response(
        request,
        503,
        "llm_configuration_error",
        "The chatbot service is not configured correctly.",
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
):
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", "http_error")
        message = exc.detail.get("message", "The request could not be completed.")
    else:
        code = "http_error"
        message = str(exc.detail)

    return error_response(
        request,
        exc.status_code,
        code,
        message,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return error_response(
        request,
        422,
        "validation_error",
        "The request contains invalid or missing fields.",
    )


# Existing health endpoint stays at /health.
app.include_router(health_router)

# Messages and chat are available under /api/v1.
app.include_router(v1_router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Netsol API"}
