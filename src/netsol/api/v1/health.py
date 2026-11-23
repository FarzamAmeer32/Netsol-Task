
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from netsol.api.dependencies import DbSession

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


@router.get("/health/ready", tags=["Health"])
async def readiness_check(db: DbSession):
    try:
        await db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "available",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            },
        )
