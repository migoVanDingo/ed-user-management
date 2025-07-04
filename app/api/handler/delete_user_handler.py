from fastapi import Request, Depends
from platform_common.db.dal.user_dal import UserDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.errors.base import NotFoundError
from platform_common.db.dependencies.get_dal import get_dal

logger = get_logger("delete_user_handler")


class DeleteUserHandler(AbstractHandler):
    """
    Handler for deleting a user by ID.
    """

    def __init__(self, user_dal: UserDAL = Depends(get_dal(UserDAL))):
        super().__init__()
        self.user_dal = user_dal

    async def do_process(self, user_id: str) -> ServiceResponse:
        deleted = await self.user_dal.delete(user_id)

        if not deleted:
            raise NotFoundError(
                message="User not found or could not be deleted", code="USER_NOT_FOUND"
            )

        return ServiceResponse(
            message="User deleted successfully",
            status_code=200,
            data={"user_id": user_id},
        )
