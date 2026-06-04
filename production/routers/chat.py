import time
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from models import ChatRequest, ChatResponse, OpenAIChatRequest
from auth import require_api_key
from database import save_message, get_history, log_usage, get_project
from services.llm import call_llm, stream_llm

router = APIRouter(prefix="/v1", tags=["Chat"])


def _resolve_project_config(project_id: str | None, api_key: str) -> dict | None:
    if not project_id:
        return None
    proj = get_project(project_id, api_key)
    if not proj:
        raise HTTPException(404, f"Project '{project_id}' not found")
    return proj


# ── Chat (native format) ─────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(require_api_key)):
    start      = time.time()
    api_key    = user["api_key"]
    session_id = req.session_id or str(uuid.uuid4())

    proj = _resolve_project_config(req.project_id, api_key)

    system_prompt = req.system_prompt
    temperature   = req.temperature
    max_tokens    = req.max_tokens
    mode          = req.mode.value

    if proj:
        system_prompt = system_prompt or proj["system_prompt"]
        temperature   = proj["temperature"]
        max_tokens    = proj["max_tokens"]

    history  = get_history(session_id, limit=20)
    messages = list(history) + [{"role": "user", "content": req.message}]

    if req.stream:
        async def event_stream():
            full_response = ""
            async for chunk in stream_llm(
                messages=messages,
                mode=mode,
                temperature=temperature,
                max_tokens=max_tokens,
                system_override=system_prompt
            ):
                full_response += chunk
                yield chunk
            save_message(api_key, session_id, "user", req.message, 0)
            save_message(api_key, session_id, "assistant", full_response, 0)
            log_usage(api_key, "/v1/chat", "text", 0,
                      int((time.time() - start) * 1000), "success")

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    response, tokens = await call_llm(
        messages=messages,
        mode=mode,
        temperature=temperature,
        max_tokens=max_tokens,
        system_override=system_prompt
    )

    save_message(api_key, session_id, "user", req.message, 0)
    save_message(api_key, session_id, "assistant", response, tokens)

    ms = int((time.time() - start) * 1000)
    log_usage(api_key, f"/v1/chat/{mode}", "text", tokens, ms, "success")

    return ChatResponse(
        response=response,
        mode=mode,
        session_id=session_id,
        tokens_used=tokens,
        response_time_ms=ms
    )


# ── OpenAI-Compatible endpoint ───────────────────────────
@router.post("/chat/completions")
async def openai_chat(req: OpenAIChatRequest, user: dict = Depends(require_api_key)):
    start   = time.time()
    api_key = user["api_key"]

    proj = _resolve_project_config(req.project_id, api_key)

    system_prompt = None
    temperature   = req.temperature
    max_tokens    = req.max_tokens

    if proj:
        system_prompt = proj["system_prompt"]
        temperature   = proj["temperature"]
        max_tokens    = proj["max_tokens"]

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    if req.stream:
        import json

        async def openai_stream():
            completion_id = "chatcmpl-" + str(uuid.uuid4()).replace("-", "")[:24]
            async for chunk in stream_llm(
                messages=messages,
                mode="chat",
                temperature=temperature,
                max_tokens=max_tokens,
                system_override=system_prompt
            ):
                if chunk == "data: [DONE]\n\n":
                    yield "data: [DONE]\n\n"
                    break
                try:
                    token = json.loads(chunk.replace("data: ", "").strip()).get("token", "")
                    delta = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "model": req.model,
                        "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(delta)}\n\n"
                except:
                    continue
            log_usage(api_key, "/v1/chat/completions", "text", 0,
                      int((time.time() - start) * 1000), "success")

        return StreamingResponse(openai_stream(), media_type="text/event-stream")

    response, tokens = await call_llm(
        messages=messages,
        mode="chat",
        temperature=temperature,
        max_tokens=max_tokens,
        system_override=system_prompt
    )

    ms = int((time.time() - start) * 1000)
    log_usage(api_key, "/v1/chat/completions", "text", tokens, ms, "success")

    return {
        "id": "chatcmpl-" + str(uuid.uuid4()).replace("-", "")[:24],
        "object": "chat.completion",
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response},
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens":     0,
            "completion_tokens": tokens,
            "total_tokens":      tokens
        },
        "response_time_ms": ms
    }


# ── Chat History ─────────────────────────────────────────
@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str, user: dict = Depends(require_api_key)):
    from database import clear_history
    clear_history(session_id)
    return {"status": "cleared", "session_id": session_id}

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, user: dict = Depends(require_api_key)):
    history = get_history(session_id, limit=50)
    return {"session_id": session_id, "messages": history}
