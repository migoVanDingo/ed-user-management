from fastapi import Request, Depends
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.errors.base import BadRequestError, NotFoundError
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.db.dal.user_dal import UserDAL

logger = get_logger("update_user_handler")


class UpdateUserHandler(AbstractHandler):
    """
    Handler for updating user information.
    """

    def __init__(self, user_dal: UserDAL = Depends(get_dal(UserDAL))):
        super().__init__()
        self.user_dal = user_dal

    async def do_process(self, request: Request, user_id: str) -> ServiceResponse:

        update_data = await request.json()

        if not update_data:
            raise BadRequestError(message="Missing update data", code="NO_UPDATE_DATA")

        # Confirm user exists before updating
        user = await self.user_dal.get_by_id(user_id)
        if not user:
            raise NotFoundError(message="User not found", code="USER_NOT_FOUND")

        # Perform the update
        updated_user = await self.user_dal.update(user_id, update_data)

        return ServiceResponse(
            message="User updated successfully",
            status_code=200,
            data=updated_user.dict(),
        )
