from fastapi import APIRouter, Body, Depends, status

from app.commons.authentication import AccessTokenAuthentication
from app.models.schema import AccessTokenSchema

from .schema import SessionRequest
from .use_cases import UpdateSession

router = APIRouter(prefix="/sessions")


@router.put(
    "",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update(
    request: SessionRequest = Body(...),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: UpdateSession = Depends(),
) -> None:
    await use_case.execute(
        schema.user_id,
        request.refresh_token,
        request.device_token,
        request.platform_type,
    )
