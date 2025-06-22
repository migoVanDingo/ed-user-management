# common/config/settings.py (or similar)

import os
from dotenv import load_dotenv

load_dotenv()  # loads .env file if present


class Settings:
    # Examples
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    # SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    # Add more config as needed


settings = Settings()
