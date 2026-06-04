import httpx
import json
import re
from typing import AsyncGenerator, List, Optional
from config import get_settings

settings = get_settings()

# ── System Prompts ───────────────────────────────────────
SYSTEM_PROMPTS = {
    "chat": """You are a helpful, accurate AI assistant.
Reply clearly and concisely. Never show your thinking process.""",

    "reason": """You are an expert reasoning assistant.
Think step by step carefully before answering.
Show your reasoning process clearly. /think""",

    "code": """You are an expert programmer.
Write clean, efficient, well-commented code.
Always explain what the code does.
Support all programming languages.""",

    "summarize": """You are an expert at summarizing documents.
Extract key points clearly and concisely.
Maintain important details and context.""",

    "translate": """You are an expert translator.
Translate accurately while maintaining context and tone.""",

    "invoice": """You are an expert invoice data extractor.
Analyze this invoice carefully and extract ONLY the fields that actually exist in the document.
Do NOT add fields that are not present in the invoice.
Do NOT use Indian tax fields (gstin, cgst, sgst, igst, hsn) unless they actually appear.

Rules:
1. Extract ONLY fields visible in the document
2. Use the exact field names from the document
3. For line items, extract only columns that exist
4. Adapt to any invoice format (US, Indian, European, etc.)
5. Return clean JSON with no empty or null fields

Return ONLY valid JSON. No explanation. No thinking.""",

    "receipt": """Extract receipt data. Return ONLY valid JSON.
{"store_name":"","date":"","time":"",
"items":[{"name":"","qty":0,"price":0}],
"subtotal":0,"tax":0,"total":0,
"payment_method":"","transaction_id":""}
Return JSON only.""",

    "id_card": """Extract ID card information. Return ONLY valid JSON.
Include all visible fields.
Return JSON only.""",

    "contract": """Extract contract details. Return ONLY valid JSON.
Include parties, dates, terms, obligations.
Return JSON only.""",

    "resume": """Extract resume information. Return ONLY valid JSON.
Include personal_info, experience, education, skills.
Return JSON only.""",

    "auto": """Analyze this document carefully.
Extract ALL information as structured JSON.
Detect document type automatically.
Return JSON only. No explanation."""
}

# ── Strip Think Tags ─────────────────────────────────────
def strip_think(content: str) -> str:
    # Remove complete think blocks
    content = re.sub(r'<think>[\s\S]*?</think>', '', content)
    # Remove orphan opening tag and everything after
    content = re.sub(r'<think>[\s\S]*', '', content)
    # Remove everything before closing tag
    content = re.sub(r'[\s\S]*?</think>', '', content)
    # Remove any remaining tags
    content = content.replace('<think>', '').replace('</think>', '')
    # Remove thinking process patterns
    content = re.sub(r"Here's a thinking process:[\s\S]*?✅\s*", '', content)
    content = re.sub(r'\*\*.*?:\*\*', '', content)
    return content.strip()

# ── Core LLM Call ────────────────────────────────────────
async def call_llm(
    messages: List[dict],
    mode: str = "chat",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    stream: bool = False,
    system_override: Optional[str] = None
) -> tuple:
    system = system_override or SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])

    full_messages = [{"role": "system", "content": system}] + messages

    # Smart thinking control
    extra = {}
    if mode in ["reason", "code"]:
        # Thinking ON — better accuracy
        extra["chat_template_kwargs"] = {"enable_thinking": True}
        temperature = 0.6
    else:
        # Thinking OFF — fast response
        extra["chat_template_kwargs"] = {"enable_thinking": False}

    payload = {
        "model":       settings.MODEL_NAME,
        "messages":    full_messages,
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "stream":      False,
        **extra
    }

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{settings.VLLM_BASE_URL}/v1/chat/completions",
            json=payload
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    tokens  = data.get("usage", {}).get("total_tokens", 0)

    # Strip think for non-reason modes
    if mode not in ["reason"]:
        content = strip_think(content)

    return content, tokens

# ── Streaming LLM ────────────────────────────────────────
async def stream_llm(
    messages: List[dict],
    mode: str = "chat",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    system_override: Optional[str] = None
) -> AsyncGenerator[str, None]:
    system = system_override or SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])

    full_messages = [{"role": "system", "content": system}] + messages

    extra = {}
    if mode in ["reason", "code"]:
        extra["chat_template_kwargs"] = {"enable_thinking": True}
        temperature = 0.6
    else:
        extra["chat_template_kwargs"] = {"enable_thinking": False}

    payload = {
        "model":       settings.MODEL_NAME,
        "messages":    full_messages,
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "stream":      True,
        **extra
    }

    think_buffer = ""
    in_think     = False

    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream(
            "POST",
            f"{settings.VLLM_BASE_URL}/v1/chat/completions",
            json=payload
        ) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data  = json.loads(data_str)
                    delta = data["choices"][0]["delta"]
                    token = delta.get("content", "")
                    if not token:
                        continue

                    if mode not in ["reason"]:
                        think_buffer += token
                        if "<think>" in think_buffer:
                            in_think = True
                        if in_think:
                            if "</think>" in think_buffer:
                                in_think     = False
                                think_buffer = think_buffer.split("</think>")[-1]
                                if think_buffer.strip():
                                    yield f"data: {json.dumps({'token': think_buffer})}\n\n"
                                think_buffer = ""
                        else:
                            yield f"data: {json.dumps({'token': think_buffer})}\n\n"
                            think_buffer = ""
                    else:
                        yield f"data: {json.dumps({'token': token})}\n\n"
                except:
                    continue

    yield "data: [DONE]\n\n"

# ── JSON Clean ───────────────────────────────────────────
def clean_json_response(content: str) -> dict:
    content = strip_think(content)
    content = re.sub(r'```json|```', '', content).strip()
    try:
        return json.loads(content)
    except:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {"raw": content}
