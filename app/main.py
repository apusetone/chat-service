import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Depends, FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter

from app.api.main import router as api_router
from app.commons.authentication import websocket_headers
from app.commons.exceptions import register_exception_handlers
from app.commons.logging import LoggingContextRoute
from app.commons.middlewares import TimeoutMiddleware
from app.commons.types import CacheType
from app.models.schema import AccessTokenSchema
from app.settings import settings
from app.ws.messages.views import WebsocketEndpointView

logging.basicConfig(level=logging.INFO)


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


app = FastAPI(title="chat-service", lifespan=lifespan)
register_exception_handlers(app)
app.add_middleware(TimeoutMiddleware, timeout=settings.REQUEST_TIMEOUT)
app.include_router(api_router, prefix="/api")
app.router.route_class = LoggingContextRoute


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
