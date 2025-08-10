from fastapi import APIRouter, Request
from fastapi.params import Depends
from structlog import get_logger
from platform_common.utils.service_response import ServiceResponse

from app.api.handler.exchange_token_handler import ExchangeFirebaseTokenHandler


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
