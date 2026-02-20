from fastapi import Depends, Request

from app.api.interface.abstract_handler import AbstractHandler
from platform_common.db.dal.organization_dal import OrganizationDAL
from platform_common.db.dal.organization_invite_dal import OrganizationInviteDAL
from platform_common.db.dependencies.get_dal import get_dal
from platform_common.errors.base import BadRequestError
from platform_common.models.organization_invite import OrganizationInvite
from platform_common.utils.invite_tokens import hash_invite_token
from platform_common.utils.service_response import ServiceResponse
from platform_common.utils.time_helpers import get_current_epoch


class ValidateTeamInviteHandler(AbstractHandler):
    def __init__(
        self,
        invite_dal: OrganizationInviteDAL = Depends(get_dal(OrganizationInviteDAL)),
        organization_dal: OrganizationDAL = Depends(get_dal(OrganizationDAL)),
    ):
        super().__init__()
        self.invite_dal = invite_dal
        self.organization_dal = organization_dal

    async def do_process(self, request: Request) -> ServiceResponse:
        token = request.query_params.get("token")
        if not token:
            raise BadRequestError(message="Missing token", code="MISSING_TOKEN")

        token_hash = hash_invite_token(token)
        invite = await self.invite_dal.get_by_token_hash(token_hash)
        if not invite:
            raise BadRequestError(
                message="Invalid invite token",
                code="INVALID_INVITE_TOKEN",
                status_code=404,
            )

        now = get_current_epoch()
        is_expired = bool(invite.expires_at and invite.expires_at < now)
        is_pending = invite.status == OrganizationInvite.Status.PENDING
        is_valid = bool(is_pending and not is_expired)

        organization = await self.organization_dal.get_by_id(invite.organization_id)

        return ServiceResponse(
            message="Invite token checked",
            status_code=200,
            data={
                "invite_id": invite.id,
                "organization_id": invite.organization_id,
                "organization_name": organization.name if organization else None,
                "email": invite.email,
                "role": invite.role,
                "status": invite.status,
                "expires_at": invite.expires_at,
                "is_expired": is_expired,
                "is_valid": is_valid,
            },
        )
