from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Avaniko AI Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Security
    SECRET_KEY: str = "change-this-to-random-64-char-string-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    API_KEY_PREFIX: str = "ava-sk-"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://avaniko:password@localhost:5432/avaniko_platform"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RunPod (private — never exposed to clients)
    RUNPOD_GATEWAY_URL: str = "http://your-runpod-ip:2222"
    RUNPOD_API_KEY: str = "sk-ava-internal-key"

    # External Providers (optional)
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_DAY: int = 10000

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
