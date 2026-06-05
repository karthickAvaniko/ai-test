import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import init_db
from config import get_settings
from routers import auth, chat, models, embeddings, api_keys, usage, projects, admin

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"[OK] {settings.APP_NAME} v{settings.VERSION} ready")
    yield
    print("[STOP] Shutting down")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
## Avaniko AI Platform API

Production-grade AI API — OpenAI-compatible.

### Base URL
`https://api.avaniko.com`

### Authentication
All AI endpoints require: `x-api-key: ava-sk-xxxx`
Dashboard endpoints require: `Authorization: Bearer <jwt_token>`

### Quick Start
1. Create account: `POST /auth/signup`
2. Create API key: `POST /v1/api-keys/create`
3. Call AI: `POST /v1/chat/completions`
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time", "X-Request-ID"]
)

from database import init_db, AsyncSessionLocal, RequestLog

# ── Request logging ────────────────────────────────────────
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start    = time.time()
    response = await call_next(request)
    ms       = int((time.time() - start) * 1000)
    response.headers["X-Response-Time"] = f"{ms}ms"

    # Log to RequestLog table
    if request.url.path.startswith(("/v1/", "/auth/")):
        try:
            async with AsyncSessionLocal() as db:
                log = RequestLog(
                    method=request.method,
                    endpoint=request.url.path,
                    response_status=response.status_code,
                    response_time_ms=ms,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent", "")
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            print(f"[Error] Logging failed: {e}")

    return response

# ── Routers ──────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(embeddings.router)
app.include_router(api_keys.router)
app.include_router(usage.router)
app.include_router(projects.router)
app.include_router(admin.router)

# ── Health ────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    import httpx
    runpod_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{settings.RUNPOD_GATEWAY_URL}/health")
            runpod_ok = r.status_code == 200
    except:
        pass
    return {
        "status":   "ok",
        "version":  settings.VERSION,
        "backend":  "ok" if runpod_ok else "degraded"
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "name":    settings.APP_NAME,
        "version": settings.VERSION,
        "docs":    "/docs",
        "api":     {
            "chat":       "POST /v1/chat/completions",
            "models":     "GET  /v1/models",
            "embeddings": "POST /v1/embeddings",
            "usage":      "GET  /v1/usage",
            "api_keys":   "POST /v1/api-keys/create",
            "projects":   "POST /v1/projects"
        }
    }

@app.exception_handler(404)
async def not_found(req, exc):
    return JSONResponse(404, {"error": "Not found", "docs": "/docs"})

@app.exception_handler(500)
async def server_error(req, exc):
    return JSONResponse(500, {"error": "Internal server error"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT,
                workers=4, loop="asyncio", access_log=True)
