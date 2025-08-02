from fastapi import Request
from platform_common.utils.service_response import ServiceResponse
from platform_common.errors.base import NotImplementedError
from app.api.interface.abstract_handler import AbstractHandler


class LogoutUserHandler(AbstractHandler):
    def __init__(self):
        pass

    async def do_process(self, request: Request) -> ServiceResponse:
        raise NotImplementedError(
            "LogoutUserHandler:(AbstractHandler):) is not implemented yet"
        )
