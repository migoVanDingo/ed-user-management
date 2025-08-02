from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from platform_common.middleware.request_id_middleware import RequestIDMiddleware
from platform_common.exception_handling.handlers import add_exception_handlers
from app.api.router.user_action_router import router as user_action_router
from app.api.router.auth_router import router as auth_router
from app.api.router.health_check import router as health_router
from app.api.router.user_router import router as user_router
from app.api.router.idp_router import router as idp_router
from app.auth.firebase_init import init_firebase

app = FastAPI(title="User Management API", version="1.0.0")
init_firebase()

origins = [
    "http://localhost:5173",  # common React dev port
    "http://127.0.0.1:5173",
    # "https://my-production-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # <-- your list here
    allow_credentials=True,  # <-- whether to expose cookies/auth headers
    allow_methods=["*"],  # <-- GET, POST, PUT, DELETE, etc
    allow_headers=["*"],  # <-- allow all headers (Authorization, Content-Type…)
)

app.add_middleware(RequestIDMiddleware)
add_exception_handlers(app)


app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(user_router, prefix="/api/user", tags=["User Management"])
app.include_router(user_action_router, prefix="/api/user/action", tags=["User Actions"])
app.include_router(idp_router, prefix="/api/idp", tags=["Identity Provider"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
