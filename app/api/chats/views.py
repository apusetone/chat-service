from fastapi import APIRouter, Body, Depends, Path, Request, status

from app.commons.authentication import AccessTokenAuthentication
from app.models.schema import AccessTokenSchema

from .schema import (
    CreateChatRequest,
    CreateChatResponse,
    ReadAllChatParticipantResponse,
    ReadAllChatRequest,
    ReadAllChatResponse,
)
from .use_cases import CreateChat, DeleteChat, ReadAllChat, ReadAllChatParticipant

router = APIRouter(prefix="/chats")


@router.get(
    "",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_200_OK,
)
async def read_all_chats(
    query_params: ReadAllChatRequest = Depends(),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: ReadAllChat = Depends(),
) -> ReadAllChatResponse:
    return ReadAllChatResponse(
        chats=[chat async for chat in use_case.execute(schema.user_id, query_params)]
    )


@router.get(
    "/{chat_id}/participants",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_200_OK,
)
async def read_all_chat_participants(
    request: Request,
    chat_id: int = Path(..., description=""),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: ReadAllChatParticipant = Depends(),
) -> ReadAllChatParticipantResponse:
    return ReadAllChatParticipantResponse(
        participants=[
            participant
            async for participant in use_case.execute(schema.user_id, chat_id)
        ]
    )


@router.post(
    "",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    request: CreateChatRequest = Body(...),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: CreateChat = Depends(),
) -> CreateChatResponse:
    return await use_case.execute(schema.user_id, request)


@router.delete(
    "/{chat_id}",
    dependencies=[
        Depends(AccessTokenAuthentication.get_current_user),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    request: Request,
    chat_id: int = Path(..., description=""),
    schema: AccessTokenSchema = Depends(AccessTokenAuthentication.get_current_user),
    use_case: DeleteChat = Depends(),
) -> None:
    await use_case.execute(schema.user_id, chat_id)
