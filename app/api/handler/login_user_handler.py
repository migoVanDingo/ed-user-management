import secrets
from fastapi import Depends, Request
from platform_common.utils.service_response import ServiceResponse
from platform_common.db.dal.user_dal import UserDAL
from platform_common.db.dal.user_session_dal import UserSessionDAL
from platform_common.errors.base import AuthError
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.utils.time_helpers import get_current_epoch
from platform_common.logging.logging import get_logger
from platform_common.auth.jwt_utils import create_jwt
from firebase_admin import auth as firebase_auth
import os

from app.api.interface.abstract_handler import AbstractHandler

logger = get_logger("login_user_handler")


class LoginUserHandler(AbstractHandler):
    def __init__(
        self,
        user_dal: UserDAL = Depends(get_dal(UserDAL)),
        session_dal: UserSessionDAL = Depends(get_dal(UserSessionDAL)),
    ):
        super().__init__()
        self.user_dal = user_dal
        self.session_dal = session_dal

    async def do_process(self, request: Request) -> ServiceResponse:
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthError("Missing or invalid Authorization header")

        id_token = authorization.replace("Bearer ", "").strip()

        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
        except Exception as e:
            logger.warning(f"Invalid Firebase token: {e}")
            raise AuthError("[Login User Handler] Invalid Firebase ID token")

        uid = decoded_token["uid"]
        user = await self.user_dal.get_by_idp_uid(uid)
        if not user:
            logger.error(f"[Login User Handler] User not found for UID: {uid}")
            raise AuthError("[Login User Handler] User not found")
        if not user.is_verified:
            logger.error(f"[Login User Handler] User not verified: {user.email}")
            raise AuthError("[Login User Handler] User not verified")

        # Create user session
        now = get_current_epoch()
        access_token_exp = 15 * 60  # 15 minutes
        refresh_token = secrets.token_urlsafe(32)
        refresh_exp = now + 30 * 24 * 60 * 60  # 30 days

        session = await self.session_dal.create_session(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=refresh_exp,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        logger.info(f"Session created: {session.id} for user {user.id}")

        token_payload = {
            "sub": user.id,
            "session_id": session.id,
        }
        access_token = create_jwt(payload=token_payload, expires_in=access_token_exp)

        is_local = os.getenv("ENVIRONMENT", "local") == "local"
        logger.info(f"is_local: {is_local}")

        service_response = ServiceResponse(
            message="Login successful",
            status_code=200,
            data={
                "access_token": access_token,
                "user": user.dict(),
            },
        )

        service_response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=not is_local,
            secure=not is_local,
            samesite="Lax" if is_local else "Strict",
            max_age=30 * 24 * 60 * 60,
            path="/auth/refresh",
        )

        logger.info(f"Access token created for user {user.id}")
        return service_response
