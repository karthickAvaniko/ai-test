import time
import uuid
import asyncio
import json
import re
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from auth import require_api_key
from database import save_message, log_usage
from services.file_parser import parse_file, detect_file_type
from services.chunker import chunk_text, estimate_tokens, merge_json_results, merge_text_results
from services.llm import call_llm, stream_llm, SYSTEM_PROMPTS, clean_json_response
from services.embedder import store_documents, search_similar
from services.ocr_service import smart_ocr, extract_text_paddle, ocr_pdf_parallel
from services.logger import logger, log_request, log_error, log_file_parse, log_llm

router = APIRouter(prefix="/v1", tags=["Files"])

async def get_file_text(content: bytes, filename: str, file_type: str) -> tuple:
    """Extract text from file — returns (text, is_image, img_b64)"""
    import base64

    if file_type == "image":
        img_b64 = base64.b64encode(content).decode()
        return "", True, img_b64

    elif file_type == "pdf":
        import fitz
        doc  = fitz.open(stream=content, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        total_pages = len(doc)
        doc.close()

        # Scanned PDF — PaddleOCR
        if len(text.strip()) < 100:
            ocr_result = await ocr_pdf_parallel(content)
            return ocr_result["full_text"], False, None
        return text, False, None

    elif file_type == "word":
        parsed = parse_file(content, filename)
        return parsed.get("total_text",""), False, None

    elif file_type == "excel":
        parsed = parse_file(content, filename)
        return parsed.get("total_text",""), False, None

    elif file_type == "audio":
        try:
            import whisper, tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(content)
                tmp = f.name
            model  = whisper.load_model("base")
            result = model.transcribe(tmp)
            os.unlink(tmp)
            return result["text"], False, None
        except Exception as e:
            return f"Audio error: {e}", False, None

    else:
        try:
            return content.decode("utf-8", errors="ignore"), False, None
        except:
            return "", False, None

@router.post("/files/ask")
async def ask_file(
    file: UploadFile = File(...),
    question: str = Form(default="Extract all information as JSON"),
    mode: str = Form(default="auto"),
    session_id: str = Form(default=""),
    stream: bool = Form(default=False),
    doc_type: str = Form(default="auto"),
    user: dict = Depends(require_api_key)
):
    start      = time.time()
    api_key    = user["api_key"]
    session_id = session_id or str(uuid.uuid4())
    content    = await file.read()
    filename   = file.filename
    file_type  = detect_file_type(filename, content)

    async def process_and_stream():
        nonlocal mode, doc_type
        full_response = ""

        try:
            log_request("/v1/files/ask", file_type, filename, api_key)
            logger.info(f"FILE | {filename} | size:{len(content)} bytes | type:{file_type}")
            # ── Step 1: Extract text ──────────────────
            text, is_image, img_b64 = await get_file_text(
                content, filename, file_type
            )

            log_file_parse(filename, file_type, len(text), len(text.strip()) < 100)
            logger.info(f"TEXT_EXTRACTED | {filename} | chars:{len(text)} | is_image:{is_image}")
            # ── Step 2: LLM decides how to respond ──
            system = f"""You are an intelligent document assistant.

The user uploaded: {filename} (type: {file_type})
User question: {question}

Instructions:
- If user asks a question (what, which, how, explain, read, analyze, type, summary) → Answer conversationally
- If user asks to extract/parse/json/get fields → Extract as JSON
- If user asks to summarize → Give a clear summary
- Always understand the user intent first
- Never blindly convert to JSON unless asked
- Respond in the same language the user used

Document content will follow. Respond appropriately."""

            # ── Step 3: Image → Vision stream ─────────
            if is_image:
                import httpx
                payload = {
                    "model": "qwen3.6-moe",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": [
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                            {"type": "text", "text": question}
                        ]}
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.0,
                    "stream": True,
                    "chat_template_kwargs": {"enable_thinking": False}
                }
                async with httpx.AsyncClient(timeout=180) as client:
                    async with client.stream(
                        "POST",
                        "http://localhost:1111/v1/chat/completions",
                        json=payload
                    ) as resp:
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "): continue
                            ds = line[6:]
                            if ds == "[DONE]": break
                            try:
                                d = json.loads(ds)
                                t = d["choices"][0]["delta"].get("content","")
                                if t:
                                    full_response += t
                                    yield f"data: {json.dumps({'token': t})}\n\n"
                            except: continue

            # ── Step 4: Text → LLM stream ─────────────
            else:
                total_tokens = estimate_tokens(text)

                if total_tokens <= 8000:
                    # Direct stream
                    messages = [{"role":"user",
                                 "content":f"{question}\n\n{text}"}]
                    async for chunk in stream_llm(
                        messages=messages,
                        mode=doc_type,
                        temperature=0.0,
                        system_override=system
                    ):
                        if chunk == "data: [DONE]\n\n":
                            break
                        try:
                            ds = chunk.replace("data: ","").strip()
                            d  = json.loads(ds)
                            t  = d.get("token","")
                            if t:
                                full_response += t
                                yield chunk
                        except: continue
                else:
                    # Large doc — chunk sequentially stream
                    chunks = chunk_text(text, chunk_size=4000)
                    for i, chunk in enumerate(chunks):
                        yield f"data: {json.dumps({'token': f'[Chunk {i+1}/{len(chunks)}] '})}\n\n"
                        messages = [{"role":"user",
                                     "content":f"{question}\n\nSection {i+1}:\n{chunk['content']}"}]
                        async for c in stream_llm(
                            messages=messages,
                            mode=doc_type,
                            temperature=0.0,
                            system_override=system
                        ):
                            if c == "data: [DONE]\n\n": break
                            try:
                                ds = c.replace("data: ","").strip()
                                d  = json.loads(ds)
                                t  = d.get("token","")
                                if t:
                                    full_response += t
                                    yield c
                            except: continue

        except Exception as e:
            yield f"data: {json.dumps({'token': f'❌ Error: {str(e)}'})}\n\n"

        finally:
            yield "data: [DONE]\n\n"
            save_message(api_key, session_id, "user",
                        f"[{filename}] {question}", 0)
            save_message(api_key, session_id, "assistant",
                        full_response, 0)
            log_usage(api_key, "/v1/files/ask", file_type, 0,
                     int((time.time()-start)*1000), "success")

    return StreamingResponse(
        process_and_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":      "no-cache",
            "X-Accel-Buffering":  "no",
            "Connection":         "keep-alive"
        }
    )

# ── RAG Store ────────────────────────────────────────────
@router.post("/files/store")
async def store_file(
    file: UploadFile = File(...),
    doc_id: str = Form(default=""),
    user: dict = Depends(require_api_key)
):
    start   = time.time()
    api_key = user["api_key"]
    doc_id  = doc_id or str(uuid.uuid4())
    content  = await file.read()
    filename = file.filename
    parsed   = parse_file(content, filename)
    text     = parsed.get("total_text","")
    if not text.strip():
        return {"status":"error","message":"No text extracted"}
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    texts  = [c["content"] for c in chunks]
    result = store_documents(texts=texts, api_key=api_key,
                             doc_id=doc_id, metadata={"filename":filename})
    return {
        "status":        "success",
        "doc_id":        doc_id,
        "chunks_stored": result.get("stored_chunks",0),
        "response_time_ms": int((time.time()-start)*1000)
    }

# ── RAG Query ────────────────────────────────────────────
@router.post("/files/query")
async def query_rag(
    question: str = Form(...),
    doc_id: str = Form(default=""),
    top_k: int = Form(default=5),
    stream: bool = Form(default=False),
    session_id: str = Form(default=""),
    user: dict = Depends(require_api_key)
):
    start      = time.time()
    api_key    = user["api_key"]
    session_id = session_id or str(uuid.uuid4())
    hits = search_similar(query=question, api_key=api_key,
                          top_k=top_k,
                          doc_id=doc_id if doc_id else None)
    if not hits:
        return {"status":"error","response":"No relevant documents found."}
    context  = "\n\n".join(f"[{i+1}]:\n{h['text']}" for i,h in enumerate(hits))
    messages = [{"role":"user",
                 "content":f"Answer based on context:\n\n{context}\n\nQuestion: {question}"}]

    async def rag_stream():
        full = ""
        async for chunk in stream_llm(messages=messages, mode="chat", temperature=0.1):
            full += chunk
            yield chunk
        save_message(api_key, session_id, "user", question, 0)
        save_message(api_key, session_id, "assistant", full, 0)

    return StreamingResponse(
        rag_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"}
    )
