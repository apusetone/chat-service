from fastapi import APIRouter, Body, Depends, status
from fastapi_limiter.depends import RateLimiter

from app.commons.authentication import (
    AccessTokenAuthentication,
    RefreshTokenAuthentication,
)
from app.models.schema import AccessTokenSchema, RefreshTokenSchema

from .schema import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshResponse,
    TwoFaRequest,
    TwoFaResponse,
)
from .use_cases import Login, Logout, Refresh, TwoFa, Unregister

router = APIRouter(prefix="/auth")


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    status_code=status.HTTP_201_CREATED,
)
async def login(
    data: LoginRequest,
    use_case: Login = Depends(Login),
) -> LoginResponse:
    return await use_case.execute(data.email)


@router.post(
    "/2fa",
    response_model=TwoFaResponse,
    dependencies=[Depends(RateLimiter(times=3, seconds=10))],
    status_code=status.HTTP_201_CREATED,
)
async def two_fa(
    data: TwoFaRequest,
    use_case: TwoFa = Depends(TwoFa),
) -> TwoFaResponse:
    return await use_case.execute(data.token, data.code)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    dependencies=[
        Depends(RateLimiter(times=3, seconds=10)),
        Depends(RefreshTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_201_CREATED,
)
async def refresh(
    data: RefreshTokenSchema = Depends(RefreshTokenAuthentication.get_current_user),
    use_case: Refresh = Depends(Refresh),
) -> RefreshResponse:
    return await use_case.execute(data.refresh_token)


@router.post(
    "/logout",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_201_CREATED,
)
async def logout(
    request: LogoutRequest = Body(...),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: Logout = Depends(),
) -> None:
    await use_case.execute(schema.user_id, schema.access_token, request.refresh_token)


@router.delete(
    "/unregister",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unregister(
    data: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: Unregister = Depends(Unregister),
) -> None:
    return await use_case.execute(data.user_id)
