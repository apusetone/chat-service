import redis.asyncio as redis
from fastapi import Depends, FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter

from app.api.main import router as api_router
from app.commons.authentication import websoket_headers
from app.commons.logging import LoggingContextRoute
from app.commons.types import CacheType
from app.models.schema import AccessTokenSchema
from app.settings import settings
from app.ws.messages.views import OldWebsocketEndpointView, WebsocketEndpointView

app = FastAPI(title="chat-service")

app.include_router(api_router, prefix="/api")
app.router.route_class = LoggingContextRoute


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
    schema: AccessTokenSchema = Depends(websoket_headers),
):
    await websocket.accept()
    # wev = OldWebsocketEndpointView()
    wev = WebsocketEndpointView()
    await wev.execute(websocket, chat_id, schema)


@app.get("/", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"message": "It works!!"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, server_header=False)
