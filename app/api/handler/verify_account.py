from fastapi import Request, Depends
from platform_common.db.dal.user_dal import UserDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.models.user import User
from platform_common.utils.time_helpers import get_current_epoch
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.db.dal.user_invite_dal import UserInviteDAL
from platform_common.db.dal.user_dal import UserDAL
from platform_common.errors.base import (
    BadRequestError,
)  # or your custom error

logger = get_logger("verify_account_handler")


class VerifyAccountHandler(AbstractHandler):
    """
    Handler for verifying a user's email address.
    """

    def __init__(
        self,
        user_dal: UserDAL = Depends(get_dal(UserDAL)),
        user_invite_dal: UserInviteDAL = Depends(get_dal(UserInviteDAL)),
    ):
        super().__init__()
        self.user_dal = user_dal
        self.user_invite_dal = user_invite_dal

    async def do_process(self, request: Request) -> ServiceResponse:
        """
        Handle the request to verify user's email address.
        """
        try:

            token = request.query_params.get("token")
            if not token:
                logger.error(f"[Verify Account Handler] Missing token in request")
                raise BadRequestError(
                    message="Missing token", code="MISSING_PARAMETERS"
                )

            user_invite = await self.user_invite_dal.get_by_token(token)
            if not user_invite:
                logger.error(f"[Verify Account Handler] Invalid token: {token}")
                raise BadRequestError(
                    message="Invalid or expired token",
                    code="INVALID_TOKEN",
                    status_code=403,
                )

            logger.info(
                f"[Verify Account Handler] expiration {user_invite.expiration} now {get_current_epoch()}"
            )
            expire = await self.user_invite_dal.expire_if_needed(
                user_invite, get_current_epoch()
            )

            logger.info(f"[Verify Account Handler] expire: {expire}")

            if expire is not None:
                logger.error(f"[Verify Account Handler] Token expired: {token}")
                raise BadRequestError(
                    message="Token has expired", code="TOKEN_EXPIRED", status_code=404
                )

            await self.user_invite_dal.redeem(user_invite)

            user_payload = {
                "email": user_invite.email,
                "idp_uid": user_invite.idp_uid,
                "username": user_invite.email.split("@")[0],  # Default username
                "is_verified": True,
            }

            user = User(**user_payload)
            user_response = await self.user_dal.create(user)

            if not user_response:
                logger.error(
                    f"[Verify Account Handler] User creation failed: {user_payload}"
                )
                raise BadRequestError(
                    message="Failed to create user", code="USER_CREATION_FAILED"
                )

            logger.info(f"[Verify Account Handler] Email verified: {user.id}")
            return ServiceResponse(
                message="Email verified successfully",
                status_code=200,
            )

        except TypeError as e:
            logger.error(f"Error verifying email: {e}")
            raise BadRequestError(message="Invalid user data", code="INVALID_PAYLOAD")
