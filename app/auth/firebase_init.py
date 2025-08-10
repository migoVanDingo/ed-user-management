# platform_common/auth/firebase_init.py
import firebase_admin
from firebase_admin import credentials
from platform_common.config.settings import get_settings
import os

from platform_common.logging.logging import get_logger
from platform_common.utils.service_response import ServiceResponse

logger = get_logger("firebase_init")
settings = get_settings()


# Only initialize once (FirebaseAdmin throws if you double-init)
def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CONFIG")
        if not cred_path:
            raise RuntimeError("FIREBASE_CONFIG is not set")

        try:
            logger.info(f"Initializing Firebase with: {cred_path}")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully.")
        except Exception as e:
            return ServiceResponse(
                {
                    "success": False,
                    "message": "Failed to initialize firebase",
                    "error": str(e),
                },
                status_code=400,
            )
