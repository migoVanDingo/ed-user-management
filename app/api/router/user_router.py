from fastapi import APIRouter, Depends, Request
from platform_common.logging.logging import get_logger
from platform_common.utils.service_response import ServiceResponse

from app.api.handler.get_user_list_handler import GetUserListHandler
from app.api.handler.get_user_handler import GetUserHandler
from app.api.handler.create_user_handler import CreateUserHandler
from app.api.handler.update_user_handler import UpdateUserHandler
from app.api.handler.delete_user_handler import DeleteUserHandler


router = APIRouter()
logger = get_logger("health")


# GET list of users
@router.get("/")
async def get_user_list(
    request: Request, handler: GetUserListHandler = Depends(GetUserListHandler)
) -> ServiceResponse:
    return await handler.do_process(request)


# GET single user by id
@router.get("/{user_id}")
async def get_user(
    user_id: str, request: Request, handler: GetUserHandler = Depends(GetUserHandler)
) -> ServiceResponse:
    return await handler.do_process(request, user_id)


# POST create a new user
@router.post("/")
async def create_user(
    request: Request, handler: CreateUserHandler = Depends(CreateUserHandler)
) -> ServiceResponse:
    return await handler.do_process(request)


# PUT update an existing user
@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: Request,
    handler: UpdateUserHandler = Depends(UpdateUserHandler),
) -> ServiceResponse:
    return await handler.do_process(request, user_id)


# DELETE remove a user
@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    handler: DeleteUserHandler = Depends(DeleteUserHandler),
) -> ServiceResponse:
    return await handler.do_process(request, user_id)
