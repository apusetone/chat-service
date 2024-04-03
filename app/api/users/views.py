from fastapi import APIRouter, Body, Depends, Request, status
from fastapi_limiter.depends import RateLimiter

from app.commons.authentication import AccessTokenAuthentication
from app.models.schema import AccessTokenSchema

from .schema import PartialUpdateUserRequest, ReadUserResponse, UpdateUserRequest
from .use_cases import PartialUpdateUser, ReadUser, UpdateUser

router = APIRouter(prefix="/users")


@router.get(
    "",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_200_OK,
)
async def read(
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: ReadUser = Depends(),
) -> ReadUserResponse:
    response = await use_case.execute(schema.user_id)
    return response


@router.put(
    "",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
        Depends(RateLimiter(times=3, seconds=10)),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update(
    request: UpdateUserRequest = Body(...),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: UpdateUser = Depends(),
) -> None:
    await use_case.execute(schema, request)


@router.patch(
    "/verify_email",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
        Depends(RateLimiter(times=3, seconds=10)),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update(
    request: PartialUpdateUserRequest = Body(...),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: PartialUpdateUser = Depends(),
) -> None:
    await use_case.execute(schema, request)
