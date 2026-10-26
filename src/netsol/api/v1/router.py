from fastapi import APIRouter

from netsol.api.v1.chat import router as chat_router
from netsol.api.v1.messages import router as messages_router

router = APIRouter(prefix="/api/v1")
router.include_router(chat_router)


router.include_router(messages_router)
router.include_router(chat_router)
