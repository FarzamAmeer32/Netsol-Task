
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for better build caching
COPY pyproject.toml uv.lock ./

# Install project dependencies without installing the project package
RUN uv sync --frozen --no-install-project

# Copy application source code
COPY src ./src

# Start the FastAPI application
CMD ["uv", "run", "--no-sync", "uvicorn", "netsol.app:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
