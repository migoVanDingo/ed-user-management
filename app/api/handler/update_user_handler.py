from fastapi import Request
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger

logger = get_logger("update_user_handler")


class UpdateUserHandler(AbstractHandler):
    """
    Handler for updating user information.
    """

    def __init__(self, payload: dict):
        super().__init__()
        self.payload = payload

    async def do_process(self, request: Request) -> ServiceResponse:
        try:
            data = await request.json()
            user_id = data.get("user_id")
            update_data = data.get("update_data")

            if not user_id or not update_data:
                raise ValueError("Missing user_id or update_data in request")

            updated_user = await self.user_service.update_user(user_id, update_data)
            return ServiceResponse(data=updated_user, status_code=200)

        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise e
