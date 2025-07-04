from fastapi import Request, Depends
from platform_common.db.dal.user_dal import UserDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.errors.base import NotFoundError
from platform_common.errors.base import BadRequestError
from platform_common.db.dependencies.get_dal import get_dal

logger = get_logger("get_user_handler")


class GetUserHandler(AbstractHandler):
    """
    Handler for retrieving a user by ID.
    """

    def __init__(self, user_dal: UserDAL = Depends(get_dal(UserDAL))):
        super().__init__()
        self.user_dal = user_dal

    async def do_process(self, request: Request) -> ServiceResponse:

        email = request.query_params.get("email")
        user_id = request.query_params.get("user_id")
        id = request.query_params.get("id")
        idpuid = request.query_params.get("idpuid")

        if not user_id and not email and not id:
            raise BadRequestError(
                message="Either user_id or email must be provided",
                code="USER_ID_OR_EMAIL_REQUIRED",
            )

        if id:
            user = await self.user_dal.get_by_id(id)

        if idpuid:
            user = await self.user_dal.get_by_idp_uid(idpuid)

        if user_id:
            user = await self.user_dal.get_by_id(user_id)

        if email:
            user = await self.user_dal.get_by_email(email)

        if not user:
            raise NotFoundError(message="User not found", code="USER_NOT_FOUND")

        return ServiceResponse(
            message="User retrieved successfully",
            status_code=200,
            data=user.dict(),
        )
