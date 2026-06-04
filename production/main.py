import os
import sys
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load env
load_dotenv("/workspace/.env")

# Add production to path
sys.path.insert(0, "/workspace/production")

from config import get_settings
from database import get_db, reset_daily_counts, init_db
from routers import chat, ocr, files, admin
from routers import projects

settings = get_settings()

# ── Startup / Shutdown ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Avaniko AI Gateway starting...")

    # Create upload dir
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)

    # Init DB (creates tables if not exist)
    try:
        init_db()
        print("✅ MySQL connected")
    except Exception as e:
        print(f"❌ MySQL error: {e}")

    # Test vLLM connection
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.VLLM_BASE_URL}/health")
            print("✅ vLLM connected")
    except:
        print("⚠️  vLLM not ready yet")

    # Daily reset scheduler
    async def daily_reset():
        while True:
            await asyncio.sleep(86400)  # 24 hours
            reset_daily_counts()
            print("✅ Daily counts reset")

    asyncio.create_task(daily_reset())
    print("✅ Avaniko AI Gateway ready!")
    print(f"📡 API Docs: http://0.0.0.0:{settings.API_PORT}/docs")

    yield

    print("👋 Shutting down...")

# ── App Init ─────────────────────────────────────────────
app = FastAPI(
    title="Avaniko AI Gateway",
    description="""
## 🚀 Avaniko AI Gateway

Production-grade AI API powered by Qwen3.6 MoE model.

### Features
- 🔐 API Key authentication
- 💬 Chat / Reasoning / Coding
- 📄 Document OCR → JSON
- 📁 All file types (PDF, Word, Excel, Image, Audio)
- 🔍 RAG (Retrieval Augmented Generation)
- 📊 Usage tracking
- ⚡ Streaming responses

### Authentication
Add `x-api-key: your-api-key` header to all requests.

### Quick Start
1. Register: `POST /admin/signup`
2. Use API key in header
3. Call any endpoint
    """,
    version="1.0.0",
    lifespan=lifespan
)

# ── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Timing Middleware ────────────────────────────
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start    = time.time()
    response = await call_next(request)
    ms       = int((time.time() - start) * 1000)
    response.headers["X-Response-Time"] = f"{ms}ms"
    return response

# ── Routers ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(chat.router)
app.include_router(ocr.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(projects.router)


# ── OpenAI-compatible models list ────────────────────────
@app.get("/v1/models", tags=["System"])
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id":       settings.MODEL_NAME,
                "object":   "model",
                "owned_by": "avaniko",
                "capabilities": ["chat", "vision", "reasoning", "code"]
            }
        ]
    }

# ── Health Check ─────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    import httpx
    vllm_status = "offline"
    db_status   = "offline"

    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.VLLM_BASE_URL}/health")
            vllm_status = "ok"
    except:
        pass

    try:
        db = get_db()
        db.close()
        db_status = "ok"
    except:
        pass

    return {
        "gateway":  "ok",
        "vllm":     vllm_status,
        "database": db_status,
        "model":    settings.MODEL_NAME,
        "version":  "1.0.0"
    }

# ── Root ─────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "name":    "Avaniko AI Gateway",
        "version": "2.0.0",
        "docs":    "/docs",
        "health":  "/health",
        "endpoints": {
            "chat":              "POST /v1/chat",
            "chat_openai":       "POST /v1/chat/completions",
            "models":            "GET  /v1/models",
            "projects_create":   "POST /v1/projects",
            "projects_list":     "GET  /v1/projects",
            "projects_get":      "GET  /v1/projects/{project_id}",
            "projects_update":   "PUT  /v1/projects/{project_id}",
            "projects_delete":   "DELETE /v1/projects/{project_id}",
            "ocr":               "POST /v1/ocr/upload",
            "ocr_b64":           "POST /v1/ocr",
            "files":             "POST /v1/files/ask",
            "rag_store":         "POST /v1/files/store",
            "rag_query":         "POST /v1/files/query",
            "signup":            "POST /admin/signup",
            "stats":             "GET  /admin/stats"
        }
    }

# ── Error Handlers ────────────────────────────────────────
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "docs": "/docs"}
    )

@app.exception_handler(500)
async def server_error(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# ── Run ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=1,
        loop="asyncio",
        access_log=True,
        log_level="info"
    )
