import os
import secrets
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    APP_NAME: str = "UDYOGSETU"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://udyogsetu:password@localhost:5432/udyogsetu"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    AUTO_GENERATED_SECRET: bool = False

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_LLM_PROVIDER: str = "gemini"

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_PROVIDER: str = "mock"

    UPLOAD_DIRECTORY: str = "/tmp/udyogsetu/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    DATA_DIRECTORY: str = "./data"

    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_ENABLED: bool = True

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        if not v:
            # noqa: RUF001 - visible warning at startup; tokens are ephemeral per-process.
            cls.AUTO_GENERATED_SECRET = True
            v = secrets.token_hex(32)
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
