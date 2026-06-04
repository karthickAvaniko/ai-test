from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, AIModel
from services.auth import require_api_key

router = APIRouter(prefix="/v1", tags=["Models"])

@router.get("/models")
async def list_models(
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    result = await db.execute(select(AIModel).where(AIModel.is_active == True))
    models = result.scalars().all()
    return {
        "object": "list",
        "data": [
            {
                "id":             m.model_id,
                "object":         "model",
                "name":           m.name,
                "context_length": m.context_length,
                "capabilities":   m.capabilities,
                "owned_by":       "avaniko"
            }
            for m in models
        ]
    }
