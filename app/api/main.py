from fastapi import APIRouter

from app.commons.logging import LoggingContextRoute

from .auth.views import router as auth_router
from .chats.views import router as chats_router
from .messages.views import router as messages_router
from .sessions.views import router as sessions_router
from .users.views import router as users_router

router = APIRouter()
router.route_class = LoggingContextRoute
router.include_router(auth_router)
router.include_router(sessions_router)
router.include_router(users_router)
router.include_router(chats_router)
router.include_router(messages_router)
