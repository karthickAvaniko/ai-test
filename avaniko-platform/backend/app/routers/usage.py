from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timedelta
from database import get_db, UsageLog, APIKey
from services.auth import require_api_key, require_jwt

router = APIRouter(prefix="/v1", tags=["Usage"])

@router.get("/usage")
async def get_usage(
    days:         int = Query(default=30, ge=1, le=90),
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(UsageLog.id).label("total_requests"),
            func.sum(UsageLog.total_tokens).label("total_tokens"),
            func.avg(UsageLog.response_time_ms).label("avg_response_ms"),
            func.sum(UsageLog.cost).label("total_cost")
        )
        .where(
            UsageLog.api_key_id == api_key_meta["key_id"],
            UsageLog.created_at >= since
        )
    )
    stats = result.one()

    # By model breakdown
    by_model = await db.execute(
        select(
            UsageLog.model_id,
            func.count(UsageLog.id).label("requests"),
            func.sum(UsageLog.total_tokens).label("tokens")
        )
        .where(UsageLog.api_key_id == api_key_meta["key_id"], UsageLog.created_at >= since)
        .group_by(UsageLog.model_id)
    )

    # Recent 10 requests
    recent = await db.execute(
        select(UsageLog)
        .where(UsageLog.api_key_id == api_key_meta["key_id"])
        .order_by(desc(UsageLog.created_at))
        .limit(10)
    )

    return {
        "period_days":       days,
        "total_requests":    stats.total_requests or 0,
        "total_tokens":      int(stats.total_tokens or 0),
        "avg_response_ms":   round(float(stats.avg_response_ms or 0), 1),
        "total_cost":        float(stats.total_cost or 0),
        "by_model":          [{"model": r.model_id, "requests": r.requests, "tokens": r.tokens}
                              for r in by_model],
        "recent_requests":   [
            {
                "endpoint":    r.endpoint,
                "model":       r.model_id,
                "tokens":      r.total_tokens,
                "ms":          r.response_time_ms,
                "status":      r.status,
                "created_at":  r.created_at
            }
            for r in recent.scalars()
        ]
    }
