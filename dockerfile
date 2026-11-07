FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency configuration
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source code
COPY src ./src

# Install the project
RUN uv sync --frozen --no-dev

# Make source package importable
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "netsol.app:app", "--host", "0.0.0.0", "--port", "8000"]