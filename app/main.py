import logging

import redis.asyncio as redis
from fastapi import Depends, FastAPI, Request, WebSocket
from fastapi.exceptions import FastAPIError, RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter

from app.api.main import router as api_router
from app.commons.authentication import websocket_headers
from app.commons.logging import LoggingContextRoute
from app.commons.types import CacheType
from app.models.schema import AccessTokenSchema
from app.settings import settings
from app.ws.messages.views import WebsocketEndpointView

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="chat-service")

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


@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(
        f"{settings.REDIS_URI}/{CacheType.THROTTLING}",
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis_connection)


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
