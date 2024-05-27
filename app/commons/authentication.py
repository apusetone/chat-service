from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from botocore.session import Session
from fastapi import (
    Depends,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.commons.redis_cache import RedisCache
from app.commons.types import CacheType
from app.models.schema import AccessTokenSchema, RefreshTokenSchema, TwoFaSchema
from app.settings import settings

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail=["Invalid authentication credentials"],
    headers={"WWW-Authenticate": "Bearer"},
)


class AccessTokenAuthentication:
    @classmethod
    async def get_current_user(
        cls,
        cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> AccessTokenSchema:
        if not cred:
            raise UNAUTHORIZED

        redis = RedisCache(cache_type=CacheType.ACCESS_TOKEN)
        result = await redis.scan_with_suffix(cred.credentials)
        if not result:
            raise UNAUTHORIZED

        return AccessTokenSchema(
            access_token=cred.credentials, user_id=result["user_id"]
        )


class TwoFaAuthentication:
    @classmethod
    async def get_current_user(
        cls,
        cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> TwoFaSchema:
        if not cred:
            raise UNAUTHORIZED

        redis = RedisCache(cache_type=CacheType.TWO_FA)
        result = await redis.get(cred.credentials)
        if not result:
            raise UNAUTHORIZED

        return TwoFaSchema(**result)


class RefreshTokenAuthentication:
    @classmethod
    async def get_current_user(
        cls,
        cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> RefreshTokenSchema:
        if not cred:
            raise UNAUTHORIZED

        return RefreshTokenSchema(refresh_token=cred.credentials)


class SignatureV4Authentication:
    def __init__(self, service: str):
        self.service = service

        # AWSのセッションと認証情報を取得
        session = Session()
        credentials = session.get_credentials()

        # SigV4Authオブジェクトを作成
        self.auth = SigV4Auth(credentials, self.service, settings.REGION)

    async def verify_signature(
        self,
        request: Request,
        cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ):
        # リクエスト情報を取得
        method = request.method
        url = str(request.url)
        headers = request.headers
        body = await request.body()

        # AWSRequestオブジェクトを作成
        aws_request = AWSRequest(method=method, url=url, data=body, headers=headers)

        try:
            # 署名を追加（これにより、正しい署名情報がヘッダーにセットされる）
            self.auth.add_auth(aws_request)
        except (NoCredentialsError, PartialCredentialsError):
            # 署名に関する例外が発生した場合のエラーハンドリング
            raise HTTPException(
                status_code=401,
                detail=["Invalid signature or credentials"],
                headers={"WWW-Authenticate": "Signature"},
            )

        # 受信した署名とサーバー側で生成した署名を比較
        received_signature = headers.get("Authorization")
        generated_signature = aws_request.headers.get("Authorization")

        if received_signature != generated_signature:
            # 署名が一致しない場合はエラーを返す
            raise HTTPException(
                status_code=401,
                detail=["Signature does not match"],
                headers={"WWW-Authenticate": "Signature"},
            )

        return True


async def websocket_headers(
    websocket: WebSocket,
    authorization: str | None = Header(default=None),
) -> AccessTokenSchema:
    if authorization:
        token = authorization[len("Bearer ") :]
    else:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid authentication credentials",
        )

    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    redis = RedisCache(cache_type=CacheType.ACCESS_TOKEN)
    result = await redis.scan_with_suffix(token)
    if not result:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return AccessTokenSchema(access_token=token, user_id=result["user_id"])
