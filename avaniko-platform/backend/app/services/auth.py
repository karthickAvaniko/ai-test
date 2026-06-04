import hashlib
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import get_db, APIKey, User
from config import get_settings

settings = get_settings()

bearer_scheme  = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

# ── Password ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

# ── JWT ──────────────────────────────────────────────────
def create_jwt(user_id: str, role: str = "user") -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

# ── API Key generation ────────────────────────────────────
def generate_api_key() -> tuple[str, str, str]:
    raw       = settings.API_KEY_PREFIX + secrets.token_urlsafe(32)
    key_hash  = hashlib.sha256(raw.encode()).hexdigest()
    key_prefix = raw[:20]
    return raw, key_hash, key_prefix

def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

# ── Require API Key ───────────────────────────────────────
async def require_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> dict:
    if not api_key:
        raise HTTPException(401, "Missing x-api-key header")
    if not api_key.startswith(settings.API_KEY_PREFIX):
        raise HTTPException(401, "Invalid API key format. Must start with 'ava-sk-'")

    key_hash = hash_api_key(api_key)
    result   = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    )
    key_row = result.scalar_one_or_none()

    if not key_row:
        raise HTTPException(401, "Invalid API key")
    if key_row.expires_at and key_row.expires_at < datetime.utcnow():
        raise HTTPException(401, "API key expired")
    if key_row.requests_today >= key_row.daily_limit:
        raise HTTPException(429, f"Daily limit of {key_row.daily_limit} requests exceeded")

    # Increment counters
    await db.execute(
        update(APIKey)
        .where(APIKey.id == key_row.id)
        .values(
            requests_today=APIKey.requests_today + 1,
            requests_month=APIKey.requests_month + 1,
            total_requests=APIKey.total_requests + 1,
            last_used_at=datetime.utcnow()
        )
    )
    await db.commit()

    return {
        "key_id":      str(key_row.id),
        "user_id":     str(key_row.user_id),
        "daily_limit": key_row.daily_limit,
        "name":        key_row.name
    }

# ── Require JWT (dashboard) ───────────────────────────────
async def require_jwt(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
    if not credentials:
        raise HTTPException(401, "Missing Authorization header")
    payload = decode_jwt(credentials.credentials)
    result  = await db.execute(
        select(User).where(
            User.id == payload["sub"],
            User.is_active == True
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found or inactive")
    return {"user_id": str(user.id), "email": user.email, "role": user.role}

async def require_admin(user: dict = Depends(require_jwt)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    return user
