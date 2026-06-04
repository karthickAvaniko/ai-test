from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from database import validate_api_key
from config import get_settings

settings = get_settings()

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def require_api_key(api_key: str = Security(api_key_header)) -> dict:
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key missing. Header: x-api-key"
        )
    if not api_key.startswith(settings.API_KEY_PREFIX):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format"
        )
    user = validate_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key / Daily limit exceeded"
        )
    return user

async def require_admin(api_key: str = Security(api_key_header)) -> bool:
    if api_key != f"admin-{settings.ADMIN_PASSWORD}":
        raise HTTPException(
            status_code=403,
            detail="Admin access only"
        )
    return True
