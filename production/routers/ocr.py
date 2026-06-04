import time
import base64
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from models import OCRRequest, OCRResponse
from auth import require_api_key
from database import log_usage
from services.ocr_service import smart_ocr, extract_with_vision
from services.llm import clean_json_response

router = APIRouter(prefix="/v1", tags=["OCR"])

# ── OCR via File Upload ──────────────────────────────────
@router.post("/ocr/upload")
async def ocr_upload(
    file: UploadFile = File(...),
    doc_type: str = Form(default="auto"),
    use_vision: bool = Form(default=True),
    user: dict = Depends(require_api_key)
):
    start   = time.time()
    api_key = user["api_key"]

    content  = await file.read()
    filename = file.filename

    result = await smart_ocr(
        file_content=content,
        filename=filename,
        doc_type=doc_type,
        use_vision=use_vision
    )

    ms = int((time.time() - start) * 1000)
    log_usage(
        api_key, "/v1/ocr/upload",
        filename.split(".")[-1],
        result.get("tokens_used", 0),
        ms, "success" if result["success"] else "error"
    )

    return {
        "status":           "success" if result["success"] else "error",
        "data":             result.get("data", {}),
        "engine":           result.get("engine", ""),
        "doc_type":         doc_type,
        "total_pages":      result.get("total_pages", 1),
        "tokens_used":      result.get("tokens_used", 0),
        "response_time_ms": ms
    }

# ── OCR via Base64 ───────────────────────────────────────
@router.post("/ocr", response_model=OCRResponse)
async def ocr_base64(
    req: OCRRequest,
    user: dict = Depends(require_api_key)
):
    start   = time.time()
    api_key = user["api_key"]

    result = await extract_with_vision(
        image_base64=req.image_base64,
        doc_type=req.doc_type.value
    )

    ms = int((time.time() - start) * 1000)
    log_usage(
        api_key, "/v1/ocr",
        "image", result.get("tokens_used", 0),
        ms, "success" if result["success"] else "error"
    )

    return OCRResponse(
        status="success" if result["success"] else "error",
        data=result.get("data", {}),
        doc_type=req.doc_type.value,
        pages_processed=1,
        response_time_ms=ms
    )

# ── Batch OCR (multiple files) ───────────────────────────
@router.post("/ocr/batch")
async def ocr_batch(
    files: list[UploadFile] = File(...),
    doc_type: str = Form(default="auto"),
    user: dict = Depends(require_api_key)
):
    start   = time.time()
    api_key = user["api_key"]
    results = []

    import asyncio
    async def process_one(file: UploadFile):
        content  = await file.read()
        filename = file.filename
        result   = await smart_ocr(
            file_content=content,
            filename=filename,
            doc_type=doc_type,
            use_vision=True
        )
        return {
            "filename": filename,
            "status":   "success" if result["success"] else "error",
            "data":     result.get("data", {}),
            "engine":   result.get("engine", ""),
            "response_time_ms": result.get("response_time_ms", 0)
        }

    # Process all files in parallel
    results = await asyncio.gather(
        *[process_one(f) for f in files]
    )

    total_ms = int((time.time() - start) * 1000)
    log_usage(
        api_key, "/v1/ocr/batch", "batch",
        0, total_ms, "success"
    )

    return {
        "status":           "success",
        "total_files":      len(files),
        "results":          results,
        "response_time_ms": total_ms
    }
