import asyncio

import boto3
from botocore.client import BaseClient

from app.commons.types import AWSServiceType


class AWSClient:
    _instances: dict[AWSServiceType, BaseClient] = {}
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def get_client(cls, service: AWSServiceType, *args, **kwargs) -> BaseClient:
        async with cls._lock:
            if service not in cls._instances:
                cls._instances[service] = boto3.client(service.value, *args, **kwargs)
            return cls._instances[service]
