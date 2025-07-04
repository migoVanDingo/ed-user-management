from fastapi import Request, Depends
from platform_common.db.dal.user_dal import UserDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.db.dependencies.get_dal import get_dal

logger = get_logger("get_user_list_handler")


class GetUserListHandler(AbstractHandler):
    """
    Handler for retrieving a list of users.
    """

    def __init__(self, user_dal: UserDAL = Depends(get_dal(UserDAL))):
        super().__init__()
        self.user_dal = user_dal

    async def do_process(self, request: Request) -> ServiceResponse:

        raw_filters = dict(request.query_params)

        # Alias map: maps incoming keys to actual model attributes
        alias_map = {
            "user_id": "id",  # map 'user_id' to 'id' (which exists in DB)
        }

        normalized_filters = {}

        for key, value in raw_filters.items():
            model_field = alias_map.get(key, key)

            # Only include valid keys for the User model
            if hasattr(self.user_dal.model, model_field):
                normalized_filters[model_field] = value
            else:
                logger.warning(f"Ignoring unsupported query param: {key}")

        users = await self.user_dal.get_list(filters=normalized_filters)

        return ServiceResponse(
            message="User list retrieved successfully",
            status_code=200,
            data=[user.dict() for user in users],
        )
