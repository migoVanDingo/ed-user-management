from fastapi import Request
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.errors.base import NotFoundError
from platform_common.logging.logging import get_logger

logger = get_logger("get_user_handler")


class GetUserHandler(AbstractHandler):
    """
    Handler for retrieving user information.
    """

    def __init__(self):
        super().__init__()

    async def do_porcess(self, request: Request) -> ServiceResponse:
        """
        Handle the request to get user information.
        """
        user_id = request.path_params.get("user_id")
        if not user_id:
            raise ValueError("User ID is required")

        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        return ServiceResponse(data=user, status_code=200)
