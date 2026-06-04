import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional
from database import get_db, APIKey
from services.auth import require_jwt, generate_api_key

router = APIRouter(prefix="/v1/api-keys", tags=["API Keys"])

class CreateKeyRequest(BaseModel):
    name:          str = "Default Key"
    daily_limit:   int = 1000
    monthly_limit: int = 30000

@router.post("/create")
async def create_key(
    req:  CreateKeyRequest,
    db:   AsyncSession = Depends(get_db),
    user: dict = Depends(require_jwt)
):
    raw, key_hash, key_prefix = generate_api_key()

    key = APIKey(
        user_id       = user["user_id"],
        key_hash      = key_hash,
        key_prefix    = key_prefix,
        name          = req.name,
        daily_limit   = req.daily_limit,
        monthly_limit = req.monthly_limit
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    return {
        "key_id":      str(key.id),
        "api_key":     raw,           # shown ONCE — never stored in plain text
        "key_prefix":  key_prefix,
        "name":        key.name,
        "daily_limit": key.daily_limit,
        "message":     "Save this key now. It will not be shown again."
    }

@router.get("")
async def list_keys(
    db:   AsyncSession = Depends(get_db),
    user: dict = Depends(require_jwt)
):
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == user["user_id"])
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return {
        "keys": [
            {
                "key_id":          str(k.id),
                "key_prefix":      k.key_prefix + "...",
                "name":            k.name,
                "is_active":       k.is_active,
                "requests_today":  k.requests_today,
                "requests_month":  k.requests_month,
                "total_requests":  k.total_requests,
                "total_tokens":    k.total_tokens,
                "daily_limit":     k.daily_limit,
                "last_used_at":    k.last_used_at,
                "created_at":      k.created_at
            }
            for k in keys
        ]
    }

@router.delete("/{key_id}")
async def revoke_key(
    key_id: str,
    db:     AsyncSession = Depends(get_db),
    user:   dict = Depends(require_jwt)
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user["user_id"])
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(404, "API key not found")

    await db.execute(
        update(APIKey).where(APIKey.id == key_id).values(is_active=False)
    )
    await db.commit()
    return {"key_id": key_id, "status": "revoked"}

@router.put("/{key_id}/limits")
async def update_limits(
    key_id:        str,
    daily_limit:   Optional[int] = None,
    monthly_limit: Optional[int] = None,
    db:            AsyncSession = Depends(get_db),
    user:          dict = Depends(require_jwt)
):
    updates = {}
    if daily_limit:   updates["daily_limit"]   = daily_limit
    if monthly_limit: updates["monthly_limit"] = monthly_limit

    await db.execute(
        update(APIKey)
        .where(APIKey.id == key_id, APIKey.user_id == user["user_id"])
        .values(**updates)
    )
    await db.commit()
    return {"key_id": key_id, "status": "updated", **updates}
