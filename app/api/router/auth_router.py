from fastapi import APIRouter, Request
from fastapi.params import Depends
from structlog import get_logger
from platform_common.utils.service_response import ServiceResponse

from app.api.handler.exchange_token_handler import ExchangeFirebaseTokenHandler
from app.api.handler.get_session_from_cookies_handler import (
    GetSessionFromCookiesHandler,
)


router = APIRouter(
    tags=["Authentication"],
)

logger = get_logger("auth")


@router.get("/exchange")
async def exchange_auth_code(
    request: Request,
    handler: ExchangeFirebaseTokenHandler = Depends(ExchangeFirebaseTokenHandler),
) -> ServiceResponse:
    """
    Exchange Firebase ID token for internal session.
    """
    try:
        logger.info("Exchanging Firebase ID token for internal session")
        return await handler.do_process(request)
    except Exception as e:
        logger.exception("Error exchanging auth code")

        return ServiceResponse(
            {
                "success": False,
                "message": "Failed to exchange auth code",
                "error": str(e),
            },
            status_code=400,
        )


@router.get("/session")
async def get_session_from_cookies(
    request: Request,
    handler: GetSessionFromCookiesHandler = Depends(GetSessionFromCookiesHandler),
) -> ServiceResponse:
    """
    Get user session from cookies.
    """
    try:
        logger.info("Getting user session from cookies")
        return await handler.do_process(request)
    except Exception as e:
        logger.exception("Error getting session from cookies")

        return ServiceResponse(
            {
                "success": False,
                "message": "Failed to get session from cookies",
                "error": str(e),
            },
            status_code=400,
        )
