from fastapi import APIRouter, Body, Depends, Path, Request, status

from app.commons.authentication import AccessTokenAuthentication
from app.models.schema import AccessTokenSchema

from .schema import (
    CreateMessageRequest,
    CreateMessageResponse,
    ReadAllMessageRequest,
    ReadAllMessageResponse,
)
from .use_cases import CreateMessage, DeleteMessage, ReadAllMessage

router = APIRouter(prefix="/messages")


@router.get(
    "/chat/{chat_id}",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_200_OK,
)
async def read_all(
    chat_id: int = Path(..., description=""),
    query_params: ReadAllMessageRequest = Depends(),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: ReadAllMessage = Depends(),
) -> ReadAllMessageResponse:
    return ReadAllMessageResponse(
        messages=[
            message
            async for message in use_case.execute(schema.user_id, chat_id, query_params)
        ]
    )


@router.post(
    "/chat/{chat_id}",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    request: CreateMessageRequest = Body(...),
    chat_id: int = Path(..., description=""),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: CreateMessage = Depends(),
) -> CreateMessageResponse:
    return await use_case.execute(schema.user_id, chat_id, request)


@router.delete(
    "/{message_id}",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    request: Request,
    message_id: int = Path(..., description=""),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: DeleteMessage = Depends(),
) -> None:
    await use_case.execute(schema.user_id, message_id)
