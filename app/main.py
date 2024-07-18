from contextlib import asynccontextmanager
from typing import Union

import redis.asyncio as redis
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.api.main import router as api_router
from app.commons.admin import admins
from app.commons.authentication import websocket_headers
from app.commons.exceptions import register_exception_handlers
from app.commons.logging import LoggingContextRoute
from app.commons.middlewares import TimeoutMiddleware
from app.commons.types import CacheType
from app.db import async_engine
from app.models.schema import AccessTokenSchema
from app.settings import settings
from app.ws.messages.views import WebsocketEndpointView

oauth = OAuth()
oauth.register(
    "google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",
    },
    redirect_uri="http://localhost:8000/auth/google",
)
google = oauth.create_client("google")


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        redirect_uri = request.url_for("login_google")
        return await google.authorize_redirect(request, redirect_uri)

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Union[bool, RedirectResponse]:
        user = request.session.get("user")
        if not user:
            redirect_uri = request.url_for("login_google")
            return await google.authorize_redirect(request, redirect_uri)

        return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPILimiter用のRedis接続
    redis_throttling_connection = redis.from_url(
        f"{settings.REDIS_URI}/{CacheType.THROTTLING}",
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis_throttling_connection)

    # FastAPICache用の別のRedis接続
    redis_cache_connection = redis.from_url(
        f"{settings.REDIS_URI}/{CacheType.CACHE}",
    )
    FastAPICache.init(RedisBackend(redis_cache_connection), prefix="fastapi-cache")

    try:
        yield
    finally:
        pass


app = FastAPI(
    title="chat-service",
    docs_url=None if settings.ENV == "prd" else "/docs",
    redoc_url=None if settings.ENV == "prd" else "/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG,
)
register_exception_handlers(app)
app.add_middleware(TimeoutMiddleware, timeout=settings.REQUEST_TIMEOUT)
app.include_router(api_router, prefix="/api")
app.router.route_class = LoggingContextRoute

# 管理画面
admin = Admin(
    app=app,
    engine=async_engine,
    authentication_backend=AdminAuth(settings.SECRET),
    base_url="/admin",
    debug=True,  # settings.DEBUG
)
admin.app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
admin.app.add_middleware(SessionMiddleware, secret_key=settings.SECRET)
for a in admins:
    admin.add_view(a)


@admin.app.route("/auth/google")
async def login_google(request: Request) -> Response:
    token = await google.authorize_access_token(request)
    user = token.get("userinfo")
    if user:
        request.session["user"] = user
    return RedirectResponse(request.url_for("admin:index"))


if settings.DEBUG:
    from debug_toolbar.middleware import DebugToolbarMiddleware

    app.add_middleware(
        DebugToolbarMiddleware,
        panels=["app.db.SQLAlchemyPanel"],
    )


# TODO: viewsに配置したかった
@app.websocket("/ws/messages/chat/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    schema: AccessTokenSchema = Depends(websocket_headers),
):
    await websocket.accept()
    wev = WebsocketEndpointView()
    await wev.execute(websocket, chat_id, schema)


@app.get("/", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"message": "It works!!"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, server_header=False)
