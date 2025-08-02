# app/api/handlers/self_register_handler.py
import time
from fastapi import Request, Depends, status
from platform_common.config.settings import get_settings
from platform_common.db.dal.user_invite_dal import UserInviteDAL
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.utils.service_response import ServiceResponse
from platform_common.utils.time_helpers import get_current_epoch
from platform_common.logging.logging import get_logger
from platform_common.errors.base import AuthError, BadRequestError
from firebase_admin import auth as firebase_auth
import httpx

from app.enum.user_enum import SYSTEM_USER_IDS

logger = get_logger("self_register_handler")


class SelfRegisterHandler:
    def __init__(
        self,
        invite_dal: UserInviteDAL = Depends(get_dal(UserInviteDAL)),
    ):
        self.invite_dal = invite_dal
        self.settings = get_settings()

    async def do_process(self, request: Request) -> ServiceResponse:
        logger.info("Processing self-registration request")
        # 1) Verify Firebase ID token
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthError("Missing or invalid Authorization header")

        id_token = auth_header.removeprefix("Bearer ").strip()
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except Exception as e:
            logger.warning(f"Invalid Firebase ID token: {e}")
            raise AuthError("Invalid Firebase ID token")

        # 2) Extract email and display name
        email = decoded.get("email")
        if not email:
            raise BadRequestError("Firebase token contains no email")

        display_name = (
            decoded.get("name") or decoded.get("displayName") or email.split("@", 1)[0]
        )

        # 3) Build invite record
        now = get_current_epoch()
        expiration = (
            now + self.settings.registration_invite_expiration_days * 24 * 60 * 60
        )

        logger.info(
            f"[SelfRegisterHandler] Invite expiration set to {expiration} for {email}"
        )

        invite = await self.invite_dal.create_invite(
            email=email,
            roles=[],  # assign roles later upon redemption
            expiration=expiration,
            invited_by=SYSTEM_USER_IDS["ROOT"],
            idp_uid=decoded["uid"],
        )
        logger.info(f"Created self-registration invite {invite.id} for {email}")

        # 4) Send verification email
        accept_link = (
            f"{self.settings.frontend_url.rstrip('/')}"
            f"/accept-invite?token={invite.token}"
        )
        email_payload = {
            "to_email": email,
            "from_email": self.settings.email_from,
            "subject": "Verify your email",
            "content": (
                f"Hi {display_name},\n\n"
                "Thanks for signing up! Please verify your email by clicking:\n\n"
                f"{accept_link}\n\n"
                f"This link expires in {self.settings.registration_invite_expiration_days} days.\n"
            ),
        }
        logger.info(f"email payload: {email_payload}")
        logger.info(
            f"notification url: {self.settings.notification_service_url}/api/notification/mailgun"
        )
        notif_url = f"{self.settings.notification_service_url}/api/notification/mailgun"
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.post(notif_url, json=email_payload)
            if resp.status_code != status.HTTP_200_OK:
                logger.error(
                    f"Failed to send verification email: {resp.status_code} {resp.text}"
                )
                return ServiceResponse(
                    message="Invite created but failed to send email",
                    status_code=status.HTTP_502_BAD_GATEWAY,
                )

        return ServiceResponse(
            message="Registration email sent; please check your inbox",
            status_code=status.HTTP_201_CREATED,
            data={"invite_id": invite.id},
        )
