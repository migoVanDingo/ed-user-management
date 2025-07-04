from fastapi import FastAPI

from app.api.router.user_router import router as user_router
from app.api.router.health_check import router as health_router
from strawberry.fastapi import GraphQLRouter
from platform_common.middleware.request_id_middleware import RequestIDMiddleware
from platform_common.exception_handling.handlers import add_exception_handlers
from app.api.router.idp_router import router as idp_router

app = FastAPI(title="Core Service")
app.add_middleware(RequestIDMiddleware)
add_exception_handlers(app)

# REST endpoints
app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(user_router, prefix="/api/user", tags=["User Management"])
app.include_router(idp_router, prefix="/api/idp", tags=["Identity Provider"])
