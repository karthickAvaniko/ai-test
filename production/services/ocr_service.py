import base64
import io
import os
import asyncio
import time
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional, List
from config import get_settings

settings = get_settings()

# ── PaddleOCR lazy load ──────────────────────────────────
_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=True,
            show_log=False
        )
    return _ocr_engine

# ── Auto detect doc type from text ──────────────────────
async def auto_detect_doc_type(text_sample: str) -> str:
    from services.llm import call_llm
    prompt = f"""Analyze this document text and classify it.
Return ONLY one word from: invoice, receipt, id_card, contract, resume, report, letter, form, table, auto

Document text (first 500 chars):
{text_sample[:500]}

Return only the classification word:"""

    try:
        result, _ = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            mode="chat",
            temperature=0.0,
            max_tokens=10
        )
        doc_type = result.strip().lower().split()[0]
        valid = ["invoice","receipt","id_card","contract",
                 "resume","report","letter","form","table","auto"]
        return doc_type if doc_type in valid else "auto"
    except:
        return "auto"

# ── Dynamic system prompt builder ────────────────────────
async def build_dynamic_prompt(
    text_sample: str,
    doc_type: str = "auto"
) -> str:
    from services.llm import call_llm

    if doc_type != "auto":
        from services.llm import SYSTEM_PROMPTS
        return SYSTEM_PROMPTS.get(doc_type, SYSTEM_PROMPTS["auto"])

    # Dynamically generate extraction prompt
    prompt = f"""You are an expert document analyzer.
Look at this document sample and create a JSON extraction schema.

Document sample:
{text_sample[:800]}

Create a system prompt that will extract ALL fields from this document type as JSON.
The prompt should be specific to this document's structure.
Return only the system prompt text:"""

    try:
        result, _ = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            mode="chat",
            temperature=0.2,
            max_tokens=500
        )
        return result.strip() + "\nReturn JSON only. No explanation."
    except:
        from services.llm import SYSTEM_PROMPTS
        return SYSTEM_PROMPTS["auto"]

# ── Image preprocess ─────────────────────────────────────
def preprocess_image(image_data: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_data))
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > 4096:
        ratio = 4096 / max(w, h)
        img = img.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)
    return np.array(img)

# ── PaddleOCR extract ────────────────────────────────────
def extract_text_paddle(image_data: bytes) -> Dict[str, Any]:
    try:
        ocr       = get_ocr_engine()
        img_array = preprocess_image(image_data)
        result    = ocr.ocr(img_array, cls=True)

        lines = []
        full_text = ""
        confidence_scores = []

        if result and result[0]:
            for line in result[0]:
                text       = line[1][0]
                confidence = line[1][1]
                lines.append({
                    "text":       text,
                    "confidence": round(confidence, 3),
                    "bbox":       line[0]
                })
                full_text += text + "\n"
                confidence_scores.append(confidence)

        avg_conf = (
            sum(confidence_scores)/len(confidence_scores)
            if confidence_scores else 0.0
        )

        return {
            "success":        True,
            "full_text":      full_text.strip(),
            "lines":          lines,
            "avg_confidence": round(avg_conf, 3),
            "total_lines":    len(lines),
            "engine":         "paddleocr-2.9.1"
        }
    except Exception as e:
        return {
            "success":        False,
            "full_text":      "",
            "lines":          [],
            "avg_confidence": 0.0,
            "error":          str(e),
            "engine":         "paddleocr-2.9.1"
        }

# ── PDF page to image ────────────────────────────────────
def pdf_page_to_image(pdf_content: bytes, page_num: int) -> bytes:
    import fitz
    doc  = fitz.open(stream=pdf_content, filetype="pdf")
    page = doc[page_num]
    mat  = fitz.Matrix(2.0, 2.0)
    pix  = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes

# ── Parallel PDF OCR ─────────────────────────────────────
async def ocr_pdf_parallel(pdf_content: bytes) -> Dict[str, Any]:
    import fitz
    doc         = fitz.open(stream=pdf_content, filetype="pdf")
    total_pages = len(doc)
    doc.close()

    loop = asyncio.get_event_loop()
    from concurrent.futures import ThreadPoolExecutor

    def process_page(page_num):
        img_bytes = pdf_page_to_image(pdf_content, page_num)
        result    = extract_text_paddle(img_bytes)
        return {
            "page":       page_num + 1,
            "text":       result["full_text"],
            "confidence": result["avg_confidence"]
        }

    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks        = [loop.run_in_executor(executor, process_page, i)
                        for i in range(total_pages)]
        page_results = await asyncio.gather(*tasks)

    page_results = sorted(page_results, key=lambda x: x["page"])
    all_text     = "\n\n".join(
        f"--- Page {p['page']} ---\n{p['text']}"
        for p in page_results
    )

    return {
        "success":     True,
        "full_text":   all_text.strip(),
        "pages":       page_results,
        "total_pages": total_pages,
        "engine":      "paddleocr-parallel"
    }

# ── Vision extract (Qwen3.6) ─────────────────────────────
async def extract_with_vision(
    image_base64: str,
    doc_type: str = "auto",
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    import httpx
    from services.llm import SYSTEM_PROMPTS, clean_json_response

    system = system_prompt or SYSTEM_PROMPTS.get(doc_type, SYSTEM_PROMPTS["auto"])

    payload = {
        "model":   settings.MODEL_NAME,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {"type": "text", "text": "Extract all information and return JSON only."}
                ]
            }
        ],
        "max_tokens":  4096,
        "temperature": 0.0,
        "chat_template_kwargs": {"enable_thinking": False}
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

    return {
        "success":     True,
        "data":        clean_json_response(content),
        "tokens_used": tokens,
        "engine":      "qwen3.6-vision"
    }

# ── MAIN: Smart dynamic OCR ──────────────────────────────
async def smart_ocr(
    file_content: bytes,
    filename: str,
    doc_type: str = "auto",
    use_vision: bool = True
) -> Dict[str, Any]:
    start = time.time()
    ext   = filename.lower().split(".")[-1]

    from services.llm import call_llm, clean_json_response, SYSTEM_PROMPTS

    # ── IMAGE ─────────────────────────────────────────
    if ext in ["png","jpg","jpeg","webp","bmp","tiff"]:
        img_b64 = base64.b64encode(file_content).decode()

        # Step 1: Quick paddle OCR to get text sample
        paddle_result = extract_text_paddle(file_content)
        text_sample   = paddle_result.get("full_text", "")

        # Step 2: Auto detect doc type if not specified
        if doc_type == "auto" and text_sample:
            doc_type = await auto_detect_doc_type(text_sample)

        # Step 3: Build dynamic prompt
        system = await build_dynamic_prompt(text_sample, doc_type)

        # Step 4: Vision extract with dynamic prompt
        if use_vision:
            result = await extract_with_vision(img_b64, doc_type, system)
        else:
            # OCR only — send text to LLM
            content, tokens = await call_llm(
                messages=[{"role": "user", "content": text_sample}],
                mode=doc_type,
                temperature=0.0,
                system_override=system
            )
            result = {
                "success":     True,
                "data":        clean_json_response(content),
                "tokens_used": tokens,
                "engine":      "paddleocr+qwen3.6"
            }

        result["doc_type_detected"] = doc_type
        result["response_time_ms"]  = int((time.time()-start)*1000)
        return result

    # ── PDF ───────────────────────────────────────────
    elif ext == "pdf":
        import fitz
        doc  = fitz.open(stream=file_content, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        total_pages = len(doc)
        doc.close()

        # Scanned PDF
        if len(text.strip()) < 100:
            ocr_result  = await ocr_pdf_parallel(file_content)
            text_sample = ocr_result["full_text"]
        else:
            text_sample = text

        # Auto detect + dynamic prompt
        if doc_type == "auto":
            doc_type = await auto_detect_doc_type(text_sample)

        system = await build_dynamic_prompt(text_sample, doc_type)

        # Chunk if large
        from services.chunker import estimate_tokens, chunk_text, merge_json_results
        import json as _json

        if estimate_tokens(text_sample) <= 8000:
            content, tokens = await call_llm(
                messages=[{"role": "user", "content": text_sample}],
                mode=doc_type,
                temperature=0.0,
                system_override=system
            )
            data = clean_json_response(content)
        else:
            # Large PDF — chunk + parallel
            chunks = chunk_text(text_sample, chunk_size=4000)

            async def process_chunk(chunk):
                c, t = await call_llm(
                    messages=[{"role": "user", "content": chunk["content"]}],
                    mode=doc_type,
                    temperature=0.0,
                    system_override=system
                )
                return clean_json_response(c), t

            results = await asyncio.gather(
                *[process_chunk(c) for c in chunks]
            )
            json_results = [r[0] for r in results]
            tokens       = sum(r[1] for r in results)
            data         = merge_json_results(json_results)

        return {
            "success":            True,
            "data":               data,
            "tokens_used":        tokens,
            "total_pages":        total_pages,
            "doc_type_detected":  doc_type,
            "engine":             "dynamic-qwen3.6",
            "response_time_ms":   int((time.time()-start)*1000)
        }

    # ── OTHER FILES ───────────────────────────────────
    else:
        return {
            "success": False,
            "data":    {},
            "error":   f"Unsupported: {ext}",
            "response_time_ms": 0
        }
