from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from database import get_db, User, APIKey, UsageLog, AIModel
from services.auth import require_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
async def global_stats(
    db:    AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    users    = await db.execute(select(func.count(User.id)))
    keys     = await db.execute(select(func.count(APIKey.id)).where(APIKey.is_active == True))
    usage    = await db.execute(
        select(func.count(UsageLog.id), func.sum(UsageLog.total_tokens))
    )
    u = usage.one()
    return {
        "total_users":    users.scalar(),
        "active_api_keys": keys.scalar(),
        "total_requests": u[0] or 0,
        "total_tokens":   int(u[1] or 0)
    }

@router.get("/users")
async def list_users(
    db:    AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    result = await db.execute(
        select(User).order_by(desc(User.created_at)).limit(100)
    )
    users = result.scalars().all()
    return {
        "users": [
            {
                "user_id":    str(u.id),
                "name":       u.name,
                "email":      u.email,
                "role":       u.role,
                "is_active":  u.is_active,
                "created_at": u.created_at
            }
            for u in users
        ]
    }

@router.put("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    db:      AsyncSession = Depends(get_db),
    admin:   dict = Depends(require_admin)
):
    await db.execute(update(User).where(User.id == user_id).values(is_active=False))
    await db.commit()
    return {"user_id": user_id, "status": "suspended"}

@router.get("/usage")
async def all_usage(
    db:    AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    result = await db.execute(
        select(UsageLog).order_by(desc(UsageLog.created_at)).limit(200)
    )
    logs = result.scalars().all()
    return {
        "logs": [
            {
                "endpoint":    l.endpoint,
                "model":       l.model_id,
                "tokens":      l.total_tokens,
                "ms":          l.response_time_ms,
                "status":      l.status,
                "created_at":  l.created_at
            }
            for l in logs
        ]
    }

class AddModelRequest(BaseModel):
    model_id:       str
    name:           str
    provider:       str
    provider_url:   Optional[str] = None
    provider_key:   Optional[str] = None
    context_length: int = 32768
    capabilities:   list = ["chat"]

@router.post("/models")
async def add_model(
    req:   AddModelRequest,
    db:    AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    model = AIModel(
        model_id       = req.model_id,
        name           = req.name,
        provider       = req.provider,
        provider_url   = req.provider_url,
        provider_key   = req.provider_key,
        context_length = req.context_length,
        capabilities   = req.capabilities
    )
    db.add(model)
    await db.commit()
    return {"model_id": req.model_id, "status": "added"}
