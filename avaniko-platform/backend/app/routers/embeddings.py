import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Union
from database import get_db
from services.auth import require_api_key
from services.gateway import get_embeddings

router = APIRouter(prefix="/v1", tags=["Embeddings"])

class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "qwen3-moe"

@router.post("/embeddings")
async def embeddings(
    req:          EmbeddingRequest,
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    texts = [req.input] if isinstance(req.input, str) else req.input
    return await get_embeddings(texts, req.model)
