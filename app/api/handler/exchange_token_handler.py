from fastapi import Request, Depends, Header
from platform_common.db.dal.user_dal import UserDAL
from platform_common.db.dal.user_session_dal import UserSessionDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.models.user import User
from platform_common.utils.time_helpers import get_current_epoch
from platform_common.models.user_session import UserSession
from platform_common.config.settings import get_settings
from platform_common.errors.base import AuthError, BadRequestError
from firebase_admin import auth as firebase_auth
from platform_common.auth.jwt_utils import create_jwt
from app.pubsub.events.user_events import publish_user_verified_event
import secrets
import time
import os


logger = get_logger("exchange_token_handler")


class ExchangeFirebaseTokenHandler(AbstractHandler):
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
            raise AuthError("Invalid Firebase ID token")

        uid = decoded_token["uid"]
        email = decoded_token.get("email")
        email_verified = decoded_token.get("email_verified", False)

        # Find or create user
        user = await self.user_dal.get_by_idp_uid(uid)
        just_created = False

        if not user:
            if not email:
                raise BadRequestError("Email required to create user")

            user = User(
                idp_uid=uid,
                email=email,
                username=email.split("@")[0],
                # ✅ keep semantics: OAuth users are verified if Firebase says so
                is_verified=email_verified,
            )
            user = await self.user_dal.create(user)
            just_created = True
            logger.info(f"Created new user from Firebase: {user.id}")

        # track previous verification state
        was_verified_before = bool(getattr(user, "is_verified", False))

        if not user.is_verified:
            if email_verified:
                user = await self.user_dal.update(user.id, {"is_verified": True})
            else:
                raise AuthError("Email not verified")

        # 🔑 If user is verified now and wasn't before, emit user_verified
        if user.is_verified and (just_created or not was_verified_before):
            org_id = getattr(user, "organization_id", None)
            logger.info(
                "Emitting user_verified event for user_id=%s organization_id=%s",
                user.id,
                org_id,
            )
            await publish_user_verified_event(
                user_id=user.id,
                organization_id=org_id,
                email=user.email,
                username=getattr(user, "username", None),
            )

        # Create user session
        now = int(get_current_epoch())
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
                "user": user.dict(),
            },
        )
        service_response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=not is_local,
            secure=not is_local,
            samesite="Lax" if is_local else "Strict",
            max_age=30 * 24 * 60 * 60,
            path="/",
        )

        service_response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=not is_local,
            secure=not is_local,
            samesite="Lax" if is_local else "Strict",
            max_age=15 * 60,
            path="/",
        )

        logger.info(f"Access token created for user {user.id}")
        return service_response
