"""
Core Gateway — receives requests, routes to correct backend provider.
RunPod URLs and provider keys NEVER leave this service.
"""
import json
import time
import httpx
from typing import AsyncGenerator, Optional
from fastapi import HTTPException
from config import get_settings

settings = get_settings()

# ── Provider routing table ────────────────────────────────
# Model ID → how to call it (all internal, never exposed)
PROVIDERS = {
    # Your RunPod models
    "qwen3-moe":     {"type": "runpod",    "url": settings.RUNPOD_GATEWAY_URL, "key": settings.RUNPOD_API_KEY},
    "llama-3.1-70b": {"type": "runpod",    "url": settings.RUNPOD_GATEWAY_URL, "key": settings.RUNPOD_API_KEY},

    # External providers (optional — keys from .env)
    "claude-3-5-sonnet-20241022": {"type": "anthropic", "url": "https://api.anthropic.com", "key": settings.ANTHROPIC_API_KEY},
    "gemini-1.5-pro":             {"type": "google",    "url": "https://generativelanguage.googleapis.com", "key": settings.GOOGLE_API_KEY},
}

def _get_provider(model_id: str) -> dict:
    provider = PROVIDERS.get(model_id)
    if not provider:
        # Default to RunPod for unknown models
        provider = {"type": "runpod", "url": settings.RUNPOD_GATEWAY_URL, "key": settings.RUNPOD_API_KEY}
    return provider

# ── Normalize to OpenAI format ────────────────────────────
def _to_openai_response(data: dict, model: str) -> dict:
    return {
        "id":      data.get("id", f"chatcmpl-avaniko"),
        "object":  "chat.completion",
        "model":   model,
        "choices": data.get("choices", [{
            "index": 0,
            "message": {
                "role":    "assistant",
                "content": data.get("response", data.get("text", ""))
            },
            "finish_reason": "stop"
        }]),
        "usage": data.get("usage", {
            "prompt_tokens":     0,
            "completion_tokens": data.get("tokens_used", 0),
            "total_tokens":      data.get("tokens_used", 0)
        })
    }

# ── Chat Completion (non-streaming) ──────────────────────
async def chat_completion(
    messages: list,
    model: str = "qwen3-moe",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    system_prompt: Optional[str] = None
) -> dict:
    provider = _get_provider(model)
    start    = time.time()

    try:
        if provider["type"] == "runpod":
            return await _call_runpod_chat(
                messages, model, temperature, max_tokens,
                system_prompt, provider
            )
        elif provider["type"] == "anthropic":
            return await _call_anthropic(messages, model, temperature, max_tokens, system_prompt, provider)
        elif provider["type"] == "google":
            return await _call_google(messages, model, temperature, max_tokens, system_prompt, provider)
        else:
            raise HTTPException(400, f"Unknown provider for model: {model}")
    except httpx.TimeoutException:
        raise HTTPException(504, "Model backend timeout — try again")
    except httpx.ConnectError:
        raise HTTPException(503, "Model backend unreachable")

# ── Streaming Chat ────────────────────────────────────────
async def chat_completion_stream(
    messages: list,
    model: str = "qwen3-moe",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    system_prompt: Optional[str] = None
) -> AsyncGenerator[str, None]:
    provider = _get_provider(model)

    if provider["type"] == "runpod":
        async for chunk in _stream_runpod(messages, model, temperature, max_tokens, system_prompt, provider):
            yield chunk
    elif provider["type"] == "anthropic":
        async for chunk in _stream_anthropic(messages, model, temperature, max_tokens, system_prompt, provider):
            yield chunk
    else:
        # Fallback: non-streaming wrapped as stream
        result = await chat_completion(messages, model, temperature, max_tokens, system_prompt)
        content = result["choices"][0]["message"]["content"]
        chunk = {
            "id": "chatcmpl-avaniko",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

# ── RunPod backend ────────────────────────────────────────
async def _call_runpod_chat(messages, model, temperature, max_tokens, system_prompt, provider) -> dict:
    payload = {
        "messages":    messages,
        "mode":        "chat",
        "temperature": temperature,
        "max_tokens":  max_tokens,
        "stream":      False
    }
    if system_prompt:
        payload["system_prompt"] = system_prompt

    # Use native /v1/chat endpoint
    msg = messages[-1]["content"] if messages else ""
    native_payload = {
        "message":     msg,
        "mode":        "chat",
        "temperature": temperature,
        "max_tokens":  max_tokens,
        "stream":      False
    }
    if system_prompt:
        native_payload["system_prompt"] = system_prompt

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{provider['url']}/v1/chat",
            headers={"x-api-key": provider["key"]},
            json=native_payload
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "id": "chatcmpl-avaniko",
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": data.get("response", "")},
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens":     0,
            "completion_tokens": data.get("tokens_used", 0),
            "total_tokens":      data.get("tokens_used", 0)
        }
    }

async def _stream_runpod(messages, model, temperature, max_tokens, system_prompt, provider):
    msg = messages[-1]["content"] if messages else ""
    payload = {
        "message":     msg,
        "mode":        "chat",
        "temperature": temperature,
        "max_tokens":  max_tokens,
        "stream":      True
    }
    if system_prompt:
        payload["system_prompt"] = system_prompt

    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream(
            "POST",
            f"{provider['url']}/v1/chat",
            headers={"x-api-key": provider["key"]},
            json=payload
        ) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break
                try:
                    data  = json.loads(data_str)
                    token = data.get("token", "")
                    if token:
                        chunk = {
                            "id": "chatcmpl-avaniko",
                            "object": "chat.completion.chunk",
                            "model": model,
                            "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception:
                    continue

# ── Anthropic backend ─────────────────────────────────────
async def _call_anthropic(messages, model, temperature, max_tokens, system_prompt, provider) -> dict:
    if not provider["key"]:
        raise HTTPException(503, "Anthropic API key not configured")

    anthropic_msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    payload = {
        "model":      model,
        "messages":   anthropic_msgs,
        "max_tokens": max_tokens,
        "temperature":temperature
    }
    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{provider['url']}/v1/messages",
            headers={"x-api-key": provider["key"], "anthropic-version": "2023-06-01"},
            json=payload
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["content"][0]["text"] if data.get("content") else ""
    usage   = data.get("usage", {})
    return {
        "id": data.get("id", "chatcmpl-avaniko"),
        "object": "chat.completion",
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens":     usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens":      usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        }
    }

async def _stream_anthropic(messages, model, temperature, max_tokens, system_prompt, provider):
    if not provider["key"]:
        raise HTTPException(503, "Anthropic API key not configured")

    anthropic_msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    payload = {
        "model": model, "messages": anthropic_msgs,
        "max_tokens": max_tokens, "temperature": temperature, "stream": True
    }
    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream(
            "POST", f"{provider['url']}/v1/messages",
            headers={"x-api-key": provider["key"], "anthropic-version": "2023-06-01"},
            json=payload
        ) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                try:
                    data  = json.loads(line[5:].strip())
                    token = data.get("delta", {}).get("text", "")
                    if token:
                        chunk = {
                            "id": "chatcmpl-avaniko", "object": "chat.completion.chunk", "model": model,
                            "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception:
                    continue
    yield "data: [DONE]\n\n"

# ── Google Gemini backend ─────────────────────────────────
async def _call_google(messages, model, temperature, max_tokens, system_prompt, provider) -> dict:
    if not provider["key"]:
        raise HTTPException(503, "Google API key not configured")

    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{provider['url']}/v1beta/models/{model}:generateContent?key={provider['key']}",
            json=payload
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["candidates"][0]["content"]["parts"][0]["text"]
    usage   = data.get("usageMetadata", {})
    return {
        "id": "chatcmpl-avaniko", "object": "chat.completion", "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens":     usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens":      usage.get("totalTokenCount", 0)
        }
    }

# ── Embeddings ────────────────────────────────────────────
async def get_embeddings(texts: list, model: str = "qwen3-moe") -> dict:
    provider = _get_provider(model)

    if provider["type"] == "runpod":
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{provider['url']}/v1/embeddings",
                headers={"x-api-key": provider["key"]},
                json={"texts": texts}
            )
            if resp.status_code != 200:
                raise HTTPException(503, "Embedding service unavailable")
            data = resp.json()
            return {
                "object": "list",
                "model":  model,
                "data":   [{"object": "embedding", "index": i, "embedding": emb}
                           for i, emb in enumerate(data.get("embeddings", []))],
                "usage":  {"prompt_tokens": sum(len(t.split()) for t in texts), "total_tokens": sum(len(t.split()) for t in texts)}
            }

    raise HTTPException(400, f"Embeddings not supported for model: {model}")
