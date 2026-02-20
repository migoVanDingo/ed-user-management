from fastapi import Request, Depends
from platform_common.db.dal.organization_invite_dal import OrganizationInviteDAL
from platform_common.db.dal.organization_member_dal import OrganizationMemberDAL
from platform_common.db.dal.user_dal import UserDAL
from platform_common.db.dal.user_session_dal import UserSessionDAL
from app.api.interface.abstract_handler import AbstractHandler
from platform_common.utils.service_response import ServiceResponse
from platform_common.logging.logging import get_logger
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.models.user import User
from platform_common.utils.time_helpers import get_current_epoch
from platform_common.errors.base import AuthError, BadRequestError
from platform_common.models.organization_invite import OrganizationInvite
from platform_common.utils.invite_tokens import hash_invite_token
from firebase_admin import auth as firebase_auth
from platform_common.auth.jwt_utils import create_jwt
from app.pubsub.events.user_events import publish_user_verified_event
import secrets
import os


logger = get_logger("exchange_token_handler")


def _is_trusted_oauth_provider(provider: str | None) -> bool:
    return provider in {"google.com", "github.com"}


class ExchangeFirebaseTokenHandler(AbstractHandler):
    def __init__(
        self,
        user_dal: UserDAL = Depends(get_dal(UserDAL)),
        session_dal: UserSessionDAL = Depends(get_dal(UserSessionDAL)),
        organization_invite_dal: OrganizationInviteDAL = Depends(
            get_dal(OrganizationInviteDAL)
        ),
        organization_member_dal: OrganizationMemberDAL = Depends(
            get_dal(OrganizationMemberDAL)
        ),
    ):
        super().__init__()
        self.user_dal = user_dal
        self.session_dal = session_dal
        self.organization_invite_dal = organization_invite_dal
        self.organization_member_dal = organization_member_dal

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
        team_invite_token = request.headers.get("x-team-invite-token")
        team_invite = None
        if team_invite_token:
            token_hash = hash_invite_token(team_invite_token)
            team_invite = await self.organization_invite_dal.get_by_token_hash(token_hash)
            if not team_invite:
                raise AuthError("Invalid team invite token")
            if team_invite.status != OrganizationInvite.Status.PENDING:
                raise AuthError("Team invite is not pending")
            if team_invite.expires_at < get_current_epoch():
                await self.organization_invite_dal.mark_expired(team_invite)
                raise AuthError("Team invite has expired")
            if not email or team_invite.email.strip().lower() != email.strip().lower():
                raise AuthError("Invite email does not match current user")

        sign_in_provider = decoded_token.get("firebase", {}).get("sign_in_provider")
        trusted_oauth = _is_trusted_oauth_provider(sign_in_provider)
        effective_email_verified = bool(
            email_verified or (trusted_oauth and email) or team_invite
        )

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
                # Treat trusted OAuth providers as verified when email is present.
                is_verified=effective_email_verified,
            )
            user = await self.user_dal.create(user)
            just_created = True
            logger.info(f"Created new user from Firebase: {user.id}")

        # track previous verification state
        was_verified_before = bool(getattr(user, "is_verified", False))

        if not user.is_verified:
            if effective_email_verified:
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

        if team_invite:
            existing_membership = await self.organization_member_dal.get_active_by_user_and_org(
                user_id=user.id,
                organization_id=team_invite.organization_id,
            )
            if existing_membership is None:
                await self.organization_invite_dal.accept_with_membership(
                    invite=team_invite,
                    accepted_user_id=user.id,
                )
            else:
                await self.organization_invite_dal.mark_accepted(
                    invite_id=team_invite.id,
                    accepted_user_id=user.id,
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
