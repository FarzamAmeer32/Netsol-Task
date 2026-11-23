
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from netsol.core.config import get_settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Generate a secure password hash."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its stored hash."""
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token


def decode_access_token(token: str) -> dict:
    """Verify a JWT and return its claims."""
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={
            "require": ["sub", "iat", "exp", "type"],
        },
    )

    return payload
