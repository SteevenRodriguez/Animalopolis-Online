from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    APP_ENV: Literal["development", "production", "test"] = "development"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str

    CORS_ORIGINS: str = ""

    STORAGE_BACKEND: Literal["s3", "local"] = "s3"
    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET: str = "animalopolis-examenes"
    S3_USE_PATH_STYLE: bool = True
    S3_PRESIGNED_EXPIRES_SECONDS: int = 300

    WHATSAPP_SERVICE_API_KEY: str

    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024
    ALLOWED_UPLOAD_MIME: str = "application/pdf,image/jpeg,image/png,image/webp"

    BOOTSTRAP_ADMIN_EMAIL: str | None = None
    BOOTSTRAP_ADMIN_PASSWORD: str | None = None
    BOOTSTRAP_ADMIN_NOMBRE: str = "Administrador"

    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_UPLOAD: str = "30/minute"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_upload_mime_list(self) -> list[str]:
        return [m.strip().lower() for m in self.ALLOWED_UPLOAD_MIME.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
