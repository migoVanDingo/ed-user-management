# app/api/router/user_action_router.py

from fastapi import APIRouter, Depends, Request
from platform_common.logging.logging import get_logger
from platform_common.utils.service_response import ServiceResponse

from app.api.handler.self_register_handler import SelfRegisterHandler
from app.api.handler.login_user_handler import LoginUserHandler
from app.api.handler.logout_user_handler import LogoutUserHandler
from app.api.handler.verify_account import VerifyAccountHandler
from app.api.handler.validate_team_invite_handler import ValidateTeamInviteHandler

router = APIRouter(
    tags=["user-actions"],
)
logger = get_logger("user_action")


@router.get("/register")
async def register_user(
    request: Request,
    handler: SelfRegisterHandler = Depends(SelfRegisterHandler),
) -> ServiceResponse:
    """
    Register a new user.
    Expects JSON body with whatever your RegisterUserHandler needs
    (e.g. username, email, password, etc.).
    """
    return await handler.do_process(request)


@router.post("/login")
async def login_user(
    request: Request,
    handler: LoginUserHandler = Depends(LoginUserHandler),
) -> ServiceResponse:
    """
    Authenticate an existing user.
    Expects JSON body with credentials (e.g. email + password).
    """
    return await handler.do_process(request)


@router.post("/logout")
async def logout_user(
    request: Request,
    handler: LogoutUserHandler = Depends(LogoutUserHandler),
) -> ServiceResponse:
    """
    Invalidate the current user’s session or token.
    Your LogoutUserHandler can pull the token from headers/cookies.
    """
    return await handler.do_process(request)


@router.get("/verify-account")
async def verify_account(
    request: Request,
    handler: VerifyAccountHandler = Depends(VerifyAccountHandler),
) -> ServiceResponse:
    """
    Verify a user's email address.
    Expects a token in the query parameters.
    """
    return await handler.do_process(request)


@router.get("/validate-team-invite")
async def validate_team_invite(
    request: Request,
    handler: ValidateTeamInviteHandler = Depends(ValidateTeamInviteHandler),
) -> ServiceResponse:
    """
    Validate organization invite token before signup flow.
    """
    return await handler.do_process(request)
