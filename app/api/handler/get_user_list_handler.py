from fastapi import Request
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger

logger = get_logger("get_user_list_handler")


class GetUserListHandler(AbstractHandler):
    """
    Handler to get a list of users.
    """

    def __init__(self):
        pass

    async def do_process(self, request: Request) -> ServiceResponse:
        """
        Handle the request to get a list of users.
        """
        try:
            users = await self.user_service.get_all_users()
            return ServiceResponse(data=users, status_code=200)
        except Exception as e:
            logger.error(f"Error fetching user list: {e}")
            raise e
