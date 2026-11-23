
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from netsol.core.security import hash_password
from netsol.db.models.user import User
from netsol.repositories.user import (
    create_user,
    get_user_by_email,
)


class EmailAlreadyRegisteredError(Exception):
    pass


class UserRegistrationError(Exception):
    pass


def normalize_email(email: str) -> str:
    local_part, domain = email.strip().rsplit("@", 1)
    return f"{local_part}@{domain.lower()}"



def is_duplicate_email_error(exc: IntegrityError) -> bool:
    """
    Detect only a PostgreSQL unique violation on the users email constraint.
    SQLAlchemy may wrap the original asyncpg exception.
    """
    pending = [exc.orig]
    visited = set()

    while pending:
        error = pending.pop()

        if error is None or id(error) in visited:
            continue

        visited.add(id(error))

        # Check the constraint directly.
        constraint_name = getattr(
            error,
            "constraint_name",
            None,
        )

        # Some PostgreSQL drivers expose it through diag.
        if constraint_name is None:
            diagnostic = getattr(error, "diag", None)
            constraint_name = getattr(
                diagnostic,
                "constraint_name",
                None,
            )

        # Only this exact constraint means duplicate email.
        if constraint_name == "users_email_key":
            return True

        # SQLAlchemy and database drivers can wrap exceptions.
        pending.append(getattr(error, "__cause__", None))
        pending.append(getattr(error, "__context__", None))
        pending.append(getattr(error, "orig", None))

    return False



async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    normalized_email = normalize_email(email)

    try:
        existing_user = await get_user_by_email(
            db,
            normalized_email,
        )

        if existing_user is not None:
            raise EmailAlreadyRegisteredError

        hashed_password = hash_password(password)

        user = await create_user(
            db,
            normalized_email,
            hashed_password,
        )

        await db.commit()
        await db.refresh(user)

        return user

    except EmailAlreadyRegisteredError:
        raise

    except IntegrityError as exc:
        await db.rollback()

        if is_duplicate_email_error(exc):
            raise EmailAlreadyRegisteredError from exc

        raise UserRegistrationError from exc

    except SQLAlchemyError as exc:
        await db.rollback()
        raise UserRegistrationError from exc
