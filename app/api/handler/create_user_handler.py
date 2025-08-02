from fastapi import Request, Depends
from platform_common.db.dal.user_dal import UserDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.models.user import User
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.db.dal.user_dal import UserDAL
from platform_common.errors.base import (
    BadRequestError,
)  # or your custom error

logger = get_logger("create_user_handler")


class CreateUserHandler(AbstractHandler):
    """
    Handler for creating a user.
    """

    def __init__(
        self,
        user_dal: UserDAL = Depends(get_dal(UserDAL)),
    ):
        super().__init__()
        self.user_dal = user_dal

    async def do_process(self, request: Request) -> ServiceResponse:
        """
        Handle the request to create a user.
        """
        try:
            payload = await request.json()
            user = User(**payload)

        except TypeError as e:
            logger.error(f"Error creating user: {e}")
            raise BadRequestError(message="Invalid user data", code="INVALID_PAYLOAD")

        created_user = await self.user_dal.create(user)
        logger.info(f"User created: {created_user.id}")
        return ServiceResponse(
            message="User created successfully",
            status_code=201,
            data=created_user.dict(),
        )
