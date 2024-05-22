import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from asyncpg.exceptions import PostgresError
from fastapi import Depends, FastAPI, Request, WebSocket
from fastapi.exceptions import FastAPIError, RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from pydantic_core._pydantic_core import ValidationError

from app.api.main import router as api_router
from app.commons.authentication import websocket_headers
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
app.add_middleware(TimeoutMiddleware, timeout=settings.REQUEST_TIMEOUT)
app.include_router(api_router, prefix="/api")
app.router.route_class = LoggingContextRoute


# Handler for RequestValidationError
@app.exception_handler(RequestValidationError)
async def bad_request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    # Log the validation errors with traceback
    logging.error("Validation error", exc_info=exc)
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "BAD_REQUEST",
            "message": "Request parameters validation failed",
            "detail": [],
        },
    )


# Handler for pydantic_core validation errors
@app.exception_handler(ValidationError)
async def pydantic_core_validation_exception_handler(
    request: Request, exc: ValidationError
):
    # Log the validation error with traceback
    logging.error("A validation error occurred", exc_info=exc)
    # Return the error response
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "BAD_REQUEST",
            "message": "Request parameters validation failed",
            "detail": [],
        },
    )


# Handler for PostgresError
@app.exception_handler(PostgresError)
async def asyncpg_exception_handler(request: Request, exc: PostgresError):
    # Log the PostgresError error with traceback
    logging.error("An internal server error occurred (Postgres error)", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred.",
            "detail": [],
        },
    )


# Handler for FastAPIError
@app.exception_handler(FastAPIError)
async def fastapi_internal_server_error_handler(request: Request, exc: FastAPIError):
    # Log the FastAPI error with traceback
    logging.error("An internal server error occurred (FastAPI error)", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred.",
            "detail": [],
        },
    )


# General exception handler for all other exceptions
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    # Log the exception details with traceback
    logging.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred.",
            "detail": [],
        },
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
