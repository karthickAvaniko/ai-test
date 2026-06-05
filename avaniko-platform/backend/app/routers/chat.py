import time
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field
from typing import Optional, List
from database import get_db, UsageLog, RequestLog, APIKey, Project
from services.auth import require_api_key
from services.gateway import chat_completion, chat_completion_stream
from services.rate_limiter import check_rate_limit

router = APIRouter(prefix="/v1", tags=["Chat"])

class Message(BaseModel):
    role:    str
    content: str

class ChatCompletionRequest(BaseModel):
    model:       str = "qwen3-moe"
    messages:    List[Message]
    stream:      bool = False
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens:  int   = Field(default=4096, ge=1, le=32000)
    project_id:  Optional[str] = None
    system:      Optional[str] = None  # inline system prompt override

async def _log_usage(db, api_key_meta, model, endpoint, prompt_t, completion_t, ms, status):
    log = UsageLog(
        api_key_id        = api_key_meta["key_id"],
        user_id           = api_key_meta["user_id"],
        model_id          = model,
        endpoint          = endpoint,
        prompt_tokens     = prompt_t,
        completion_tokens = completion_t,
        total_tokens      = prompt_t + completion_t,
        response_time_ms  = ms,
        status            = status
    )
    db.add(log)
    # Update total tokens on key
    await db.execute(
        update(APIKey)
        .where(APIKey.id == api_key_meta["key_id"])
        .values(total_tokens=APIKey.total_tokens + prompt_t + completion_t)
    )
    await db.commit()

@router.post("/chat/completions")
async def chat_completions(
    req:          ChatCompletionRequest,
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    start = time.time()
    await check_rate_limit(api_key_meta["key_id"], limit=60, window=60)

    messages       = [{"role": m.role, "content": m.content} for m in req.messages]
    system_prompt  = req.system
    model          = req.model

    # Load project config if project_id provided
    if req.project_id:
        result  = await db.execute(
            select(Project).where(
                Project.project_id == req.project_id,
                Project.user_id    == api_key_meta["user_id"],
                Project.is_active  == True
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(404, f"Project '{req.project_id}' not found")
        system_prompt = system_prompt or project.system_prompt
        model         = project.model_id

    if req.stream:
        async def stream_response():
            try:
                tokens = 0
                async for chunk in chat_completion_stream(
                    messages=messages, model=model,
                    temperature=req.temperature, max_tokens=req.max_tokens,
                    system_prompt=system_prompt
                ):
                    if chunk != "data: [DONE]\n\n":
                        try:
                            d = json.loads(chunk[6:].strip())
                            tokens += len(d.get("choices", [{}])[0].get("delta", {}).get("content", "").split())
                        except:
                            pass
                    yield chunk

                ms = int((time.time() - start) * 1000)
                await _log_usage(db, api_key_meta, model, "/v1/chat/completions", 0, tokens, ms, "success")
            except Exception as e:
                import traceback
                traceback.print_exc()
                err = {"error": {"message": str(e), "type": "gateway_error"}}
                yield f"data: {json.dumps(err)}\n\n"

        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    result = await chat_completion(
        messages=messages, model=model,
        temperature=req.temperature, max_tokens=req.max_tokens,
        system_prompt=system_prompt
    )

    ms    = int((time.time() - start) * 1000)
    usage = result.get("usage", {})
    await _log_usage(
        db, api_key_meta, model, "/v1/chat/completions",
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
        ms, "success"
    )
    result["response_time_ms"] = ms
    return result
