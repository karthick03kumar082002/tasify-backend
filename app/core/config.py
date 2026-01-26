from functools import lru_cache
import secrets
from decouple import config, Csv
from pydantic_settings import BaseSettings
from pathlib import Path
import cloudinary
import os

class Settings(BaseSettings):
    """
    Application configuration settings.
    Reads environment variables using python-decouple.
    """

    # -------------------------
    # Project Metadata
    # -------------------------
    PROJECT_NAME: str = config("PROJECT_NAME", default="FastAPI User Project")
    DESCRIPTION: str = config("PROJECT_DESCRIPTION", default="FastAPI + PostgreSQL + Alembic Example")
    VERSION: str = config("PROJECT_VERSION", default="1.0.0")
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = config("DEBUG", default=True, cast=bool)

    # -------------------------
    # Database
    # -------------------------
    DATABASE_URL: str = config(
        "DATABASE_URL"
        # default="postgresql+asyncpg://postgres:password@localhost:5432/fastapi_db"
    )
    SYNC_DATABASE_URL: str = config(
        "SYNC_DATABASE_URL"
        # default="postgresql+psycopg2://postgres:password@localhost:5432/fastapi_db"
    )
    # Alembic should always use SYNC_DATABASE_URL

    # -------------------------
    # Security
    # -------------------------
    SECRET_KEY: str = config("SECRET_KEY", default=secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=60 * 24, cast=int)
    ALGORITHM: str = config("ALGORITHM", default="HS256")

    # -------------------------
    # CORS Settings
    # -------------------------
    # BACKEND_CORS_ORIGINS: list[str] = config(
    #     "BACKEND_CORS_ORIGINS",
    #     default="http://localhost,http://localhost:3000,http://127.0.0.1:3000",
    #     cast=Csv()
    # ) or ["http://localhost", "http://localhost:3000", "http://127.0.0.1:3000"]
    # BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # -------------------------
    # Email Settings
    # -------------------------
    SMTP_TLS: bool = config("SMTP_TLS", default=True, cast=bool)
    SMTP_PORT: int = config("SMTP_PORT", default=587, cast=int)
    SMTP_HOST: str = config("SMTP_HOST", default="")
    SMTP_USER: str = config("SMTP_USER", default="")
    SMTP_PASSWORD: str = config("SMTP_PASSWORD", default="")
    EMAILS_FROM_EMAIL: str = config("EMAILS_FROM_EMAIL", default="")
    EMAILS_FROM_NAME: str = config("EMAILS_FROM_NAME", default="Zenthogen")
# -------------------------
# Railway settins
# -------------------------

cloudinary.config(
    cloud_name=config("CLOUDINARY_CLOUD_NAME"),
    api_key=config("CLOUDINARY_API_KEY"),
    api_secret=config("CLOUDINARY_API_SECRET"),
    secure=True
)


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
