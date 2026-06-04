import time
from fastapi import APIRouter, Depends, HTTPException
from auth import require_admin, require_api_key
from database import (
    generate_api_key, get_db,
    get_usage_stats, reset_daily_counts
)
from models import RegisterRequest, RegisterResponse, UsageResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

# ── Register New API Key ─────────────────────────────────
@router.post("/register", response_model=RegisterResponse)
async def register(
    req: RegisterRequest,
    _: bool = Depends(require_admin)
):
    api_key = generate_api_key(
        user_name=req.user_name,
        user_email=req.user_email,
        daily_limit=req.daily_limit
    )
    return RegisterResponse(
        api_key=api_key,
        user_name=req.user_name,
        user_email=req.user_email,
        daily_limit=req.daily_limit
    )

# ── List All API Keys ────────────────────────────────────
@router.get("/keys")
async def list_keys(_: bool = Depends(require_admin)):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT id, user_name, user_email,
                       is_active, requests_today,
                       total_requests, daily_limit,
                       created_at
                FROM api_keys
                ORDER BY created_at DESC
            """)
            return {"keys": cur.fetchall()}
    finally:
        db.close()

# ── Get Single Key Info ──────────────────────────────────
@router.get("/keys/{api_key}")
async def get_key(
    api_key: str,
    _: bool = Depends(require_admin)
):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT * FROM api_keys
                WHERE api_key = %s
            """, (api_key,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "API key not found")
            return row
    finally:
        db.close()

# ── Disable API Key ──────────────────────────────────────
@router.put("/keys/{api_key}/disable")
async def disable_key(
    api_key: str,
    _: bool = Depends(require_admin)
):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                UPDATE api_keys
                SET is_active = FALSE
                WHERE api_key = %s
            """, (api_key,))
        return {"status": "disabled", "api_key": api_key}
    finally:
        db.close()

# ── Enable API Key ───────────────────────────────────────
@router.put("/keys/{api_key}/enable")
async def enable_key(
    api_key: str,
    _: bool = Depends(require_admin)
):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                UPDATE api_keys
                SET is_active = TRUE
                WHERE api_key = %s
            """, (api_key,))
        return {"status": "enabled", "api_key": api_key}
    finally:
        db.close()

# ── Update Daily Limit ───────────────────────────────────
@router.put("/keys/{api_key}/limit")
async def update_limit(
    api_key: str,
    daily_limit: int,
    _: bool = Depends(require_admin)
):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                UPDATE api_keys
                SET daily_limit = %s
                WHERE api_key = %s
            """, (daily_limit, api_key))
        return {
            "status":      "updated",
            "api_key":     api_key,
            "daily_limit": daily_limit
        }
    finally:
        db.close()

# ── Delete API Key ───────────────────────────────────────
@router.delete("/keys/{api_key}")
async def delete_key(
    api_key: str,
    _: bool = Depends(require_admin)
):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                DELETE FROM api_keys
                WHERE api_key = %s
            """, (api_key,))
        return {"status": "deleted", "api_key": api_key}
    finally:
        db.close()

# ── Usage Stats (per key) ────────────────────────────────
@router.get("/usage/{api_key}")
async def usage_stats(
    api_key: str,
    _: bool = Depends(require_admin)
):
    stats = get_usage_stats(api_key)
    db    = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT requests_today, daily_limit
                FROM api_keys WHERE api_key = %s
            """, (api_key,))
            row = cur.fetchone()
        return {
            "api_key":         api_key,
            "total_requests":  stats["total_requests"] or 0,
            "total_tokens":    stats["total_tokens"] or 0,
            "avg_response_ms": round(stats["avg_response_ms"] or 0, 1),
            "requests_today":  row["requests_today"] if row else 0,
            "daily_limit":     row["daily_limit"] if row else 0
        }
    finally:
        db.close()

# ── Global Stats ─────────────────────────────────────────
@router.get("/stats")
async def global_stats(_: bool = Depends(require_admin)):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total_keys,
                    SUM(total_requests) as total_requests,
                    SUM(requests_today) as requests_today
                FROM api_keys
            """)
            key_stats = cur.fetchone()
            cur.execute("""
                SELECT
                    SUM(tokens_used) as total_tokens,
                    AVG(response_time_ms) as avg_response_ms,
                    COUNT(*) as total_calls
                FROM usage_logs
            """)
            usage = cur.fetchone()
        return {
            "total_keys":      key_stats["total_keys"],
            "total_requests":  key_stats["total_requests"] or 0,
            "requests_today":  key_stats["requests_today"] or 0,
            "total_tokens":    usage["total_tokens"] or 0,
            "avg_response_ms": round(usage["avg_response_ms"] or 0, 1),
            "total_api_calls": usage["total_calls"] or 0
        }
    finally:
        db.close()

# ── Reset Daily Counts ───────────────────────────────────
@router.post("/reset-daily")
async def reset_daily(_: bool = Depends(require_admin)):
    reset_daily_counts()
    return {"status": "daily counts reset"}

# ── Self Register (public) ───────────────────────────────
@router.post("/signup", response_model=RegisterResponse)
async def public_signup(req: RegisterRequest):
    # Check if email exists
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT id FROM api_keys
                WHERE user_email = %s
            """, (req.user_email,))
            if cur.fetchone():
                raise HTTPException(
                    400, "Email already registered"
                )
    finally:
        db.close()

    api_key = generate_api_key(
        user_name=req.user_name,
        user_email=req.user_email,
        daily_limit=1000
    )
    return RegisterResponse(
        api_key=api_key,
        user_name=req.user_name,
        user_email=req.user_email,
        daily_limit=1000,
        message="Welcome! Your API key is ready."
    )
