# app/api/controller/health_check.py
from fastapi import APIRouter, Request
from fastapi.params import Depends
from platform_common.logging.logging import get_logger
from platform_common.utils.service_response import ServiceResponse
from platform_common.errors.base import AuthError

router = APIRouter()
logger = get_logger("health")


@router.get("/")
async def health_check(request: Request):

    logger.info("Health check yuh mama!", path=request.url.path)

    return ServiceResponse(message="Service is healthy", status_code=200)
