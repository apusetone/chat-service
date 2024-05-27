import datetime
import json
import sys
import time
from logging import DEBUG, StreamHandler, getLogger
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

logger = getLogger(__name__)
handler = StreamHandler(sys.stdout)
handler.setLevel(DEBUG)
logger.addHandler(handler)
logger.setLevel(DEBUG)


class LoggingContextRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = round(time.time() - before, 4)

            record = {}
            time_local = datetime.datetime.fromtimestamp(before)
            record["time_local"] = time_local.isoformat()
            if await request.body():
                # TODO: need masking
                record["request_body"] = (await request.body()).decode("utf-8")
            # TODO: need masking
            record["request_headers"] = {
                k.decode("utf-8"): v.decode("utf-8") for (k, v) in request.headers.raw
            } # type: ignore
            record["remote_addr"] = request.client.host # type: ignore
            record["request_uri"] = request.url.path
            record["request_method"] = request.method
            record["request_time"] = str(duration) # type: ignore
            record["status"] = response.status_code # type: ignore
            # TODO: need masking
            record["response_body"] = response.body.decode("utf-8")
            record["response_headers"] = {
                k.decode("utf-8"): v.decode("utf-8") for (k, v) in response.headers.raw
            } # type: ignore
            logger.info(json.dumps(record, ensure_ascii=False))
            return response

        return custom_route_handler
