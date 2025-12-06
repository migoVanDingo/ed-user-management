from fastapi import Request, Depends
from platform_common.db.dal.user_dal import UserDAL
from platform_common.db.dal.user_session_dal import UserSessionDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.utils.time_helpers import get_current_epoch
from platform_common.errors.base import AuthError
from platform_common.auth.jwt_utils import create_jwt
from platform_common.auth.token_sources import issue_access_token
import os

logger = get_logger("get_session_handler")


class GetSessionFromCookiesHandler(AbstractHandler):
    def __init__(
        self,
        user_dal: UserDAL = Depends(get_dal(UserDAL)),
        session_dal: UserSessionDAL = Depends(get_dal(UserSessionDAL)),
    ):
        super().__init__()
        self.user_dal = user_dal
        self.session_dal = session_dal

    async def do_process(self, request: Request) -> ServiceResponse:
        """
        Validate the current user session using the refresh token stored in cookies.

        This is intended for things like:
          - Frontend loaders calling `/auth/session` to see if the user is authenticated.

        Expected cookies:
          - refresh_token=<refresh token string>
        """
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            logger.info("No refresh_token cookie present")
            raise AuthError("Not authenticated")

        # Find active, non-revoked session by refresh token
        session = await self.session_dal.get_by_refresh_token(refresh_token)
        if not session:
            logger.info("No active session found for given refresh token")
            raise AuthError("Not authenticated")

        now = int(get_current_epoch())
        if session.expires_at <= now:
            logger.info(f"Session expired for session {session.id}")
            # You may optionally revoke here
            await self.session_dal.revoke_session(session.id)
            raise AuthError("Session expired")

        # Load user
        user = await self.user_dal.get_by_id(session.user_id)
        if not user:
            logger.error(
                "User not found for valid session. "
                f"session_id={session.id}, user_id={session.user_id}"
            )
            raise AuthError("User not found")

        # Optionally update last_active_at
        await self.session_dal.update_last_active(session.id)

        is_local = os.getenv("ENVIRONMENT", "local") == "local"

        service_response = ServiceResponse(
            message="Session valid",
            status_code=200,
            success=True,
            data={
                "user": user.dict(),
                "session_id": session.id,
            },
        )

        issue_access_token(
            response=service_response,
            user_id=user.id,
            session_id=session.id,
            # further tuning: could choose a shorter expiry here if desired
        )

        return service_response
