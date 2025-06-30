from fastapi import Request
from platform_common.utils.service_response import ServiceResponse
from app.api.interface.abstract_handler import AbstractHandler


class DeleteUserHandler(AbstractHandler):
    """
    Handler for deleting a user.
    """

    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id

    async def do_process(self, request: Request) -> ServiceResponse:
        """
        Handle the delete user request.
        """
        user_id = request.path_params.get("user_id")

        return ServiceResponse(message="User deleted successfully", status_code=204)
