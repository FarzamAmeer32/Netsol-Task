# Netsol API

A backend API built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. The project follows a modular architecture and includes user registration, secure authentication, protected routes, database migrations, and LLM-powered chat functionality.

## Features

- **FastAPI** REST API with versioned endpoints.
- **User registration** with email normalization and password validation.
- **Secure password hashing** using Argon2.
- **JWT authentication** using PyJWT.
- **Protected endpoints** using FastAPI dependency injection.
- **PostgreSQL** database integration.
- **SQLAlchemy 2.x** asynchronous database operations.
- **Alembic** database migrations.
- **LLM integration** using the Google Gemini SDK.
- Centralized exception handling and consistent API error responses.
- Request ID middleware for request tracking.
- Automated tests using pytest.
- Docker and Docker Compose configuration.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| PostgreSQL | Relational database |
| SQLAlchemy 2.x | Async ORM |
| Alembic | Database migrations |
| Pydantic | Data validation and settings |
| PyJWT | JWT token generation and verification |
| pwdlib / Argon2 | Password hashing |
| Google Gemini SDK | LLM integration |
| pytest | Automated testing |
| uv | Python dependency management |
| Docker | Containerization |

## Project Structure

```text
Netsol/
│
├── src/
│   └── netsol/
│       ├── app.py
│       │
│       ├── api/
│       │   ├── dependencies.py
│       │   └── v1/
│       │       ├── router.py
│       │       ├── auth.py
│       │       ├── users.py
│       │       └── chat.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   └── exceptions.py
│       │
│       ├── db/
│       │   ├── base.py
│       │   └── session.py
│       │
│       ├── repositories/
│       │   └── user.py
│       │
│       ├── schemas/
│       │   ├── auth.py
│       │   ├── user.py
│       │   └── chat.py
│       │
│       └── services/
│           ├── auth.py
│           ├── user.py
│           └── llm.py
│
├── alembic/
│   └── versions/
│
├── test/
│   ├── conftest.py
│   ├── test_auth.py
│   └── ...
│
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- uv
- Google Gemini API key

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Netsol
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file in the project root.

```env
GEMINI_API_KEY=your-gemini-api-key

DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/netsol

JWT_SECRET_KEY=your-generated-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

Generate a strong JWT secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Never commit your actual `.env` file or expose your API keys and JWT secret.

### 4. Set up the database

Create a PostgreSQL database named `netsol`.

Run database migrations:

```bash
uv run alembic upgrade head
```

### 5. Start the application

```bash
uv run uvicorn netsol.app:app --reload --app-dir src
```

The API will be available at:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

## API Endpoints

All versioned endpoints use the `/api/v1` prefix.

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API health |

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Authenticate and receive a JWT |

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users/me` | Retrieve the authenticated user's profile |

### Messages and Chat

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/messages` | List messages |
| POST | `/api/v1/messages` | Create a message |
| GET | `/api/v1/messages/{message_id}` | Retrieve a message |
| PUT | `/api/v1/messages/{message_id}` | Update a message |
| DELETE | `/api/v1/messages/{message_id}` | Delete a message |
| POST | `/api/v1/chat` | Generate an LLM-powered response |

Refer to Swagger UI at `/docs` for the exact request and response schemas.

## JWT Authentication

The application uses JSON Web Tokens for stateless access authentication.

### Login Flow

1. The user submits their email and password.
2. The email is normalized.
3. The user is retrieved from PostgreSQL.
4. The submitted password is verified against the stored Argon2 hash.
5. Inactive users and invalid credentials are rejected.
6. A signed JWT access token is generated.

Example successful login response:

```json
{
  "access_token": "your-jwt-access-token",
  "token_type": "bearer",
  "expires_in": 900
}
```

The access token contains:

- `sub`: User UUID.
- `iat`: Token issued-at timestamp.
- `exp`: Token expiration timestamp.
- `type`: Token type (`access`).

The default access-token lifetime is 15 minutes and can be configured through environment variables.

### Protected Routes

Protected endpoints use the `get_current_user` dependency.

For example:

```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

The dependency verifies the token signature, expiration, claims, and token type, then retrieves the corresponding user from the database.

It also rejects missing, invalid, expired, or tampered tokens, as well as deleted or inactive users.

The API returns a consistent `401 Unauthorized` response for authentication failures.

## Database Migrations

Alembic manages database schema changes.

Apply migrations:

```bash
uv run alembic upgrade head
```

Generate a new migration:

```bash
uv run alembic revision --autogenerate -m "migration_description"
```

Rollback one migration:

```bash
uv run alembic downgrade -1
```

## Running Tests

Run the complete test suite:

```bash
uv run pytest -q
```

Run authentication tests:

```bash
uv run pytest test/test_auth.py -q
```

**Important:** Tests use a dedicated `netsol_test` database. Configure `TEST_DATABASE_URL` if needed, and never point the test suite at your development or production database.

The test suite covers registration, password security, login, JWT validation, protected routes, inactive and deleted users, and error handling.

## Docker

Build and start the services:

```bash
docker compose up --build
```

Stop the services:

```bash
docker compose down
```

## Security Considerations

- Passwords are stored as Argon2 hashes, never as plaintext.
- JWT secrets are supplied through environment variables.
- Access tokens have a configurable expiration time.
- Token signatures and expiration are verified before accessing protected resources.
- The application checks the user's current database status on authenticated requests.
- Unknown email addresses and incorrect passwords return the same generic login error.
- A precomputed dummy password hash is used for unknown-user verification to reduce timing differences.
- Sensitive credentials and tokens should never be logged or committed to version control.

## License

This project is intended for learning and backend development purposes.