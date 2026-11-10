
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from netsol.repositories.user import get_user_by_email
from netsol.services.user import normalize_email


# Created once when this module loads, not on every login request.
DUMMY_PASSWORD_HASH = hash_password(
    "netsol-dummy-password-not-used-by-any-account"
)


class InvalidCredentialsError(Exception):
    pass


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> str:
    normalized_email = normalize_email(email)

    user = await get_user_by_email(
        db,
        normalized_email,
    )

    # Unknown email: perform a dummy password verification.
    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise InvalidCredentialsError

    # Existing email: verify against the actual stored hash.
    password_is_valid = verify_password(
        password,
        user.password_hash,
    )

    # Use the same error for wrong passwords and inactive accounts.
    if not password_is_valid or not user.is_active:
        raise InvalidCredentialsError

    # Successful login: generate the user's access token.
    return create_access_token(str(user.id))
