import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field
from typing import Optional
from database import get_db, Project
from services.auth import require_api_key, require_jwt

router = APIRouter(prefix="/v1/projects", tags=["Projects"])

class ProjectCreate(BaseModel):
    name:          str
    system_prompt: str
    description:   Optional[str] = ""
    model_id:      str = "qwen3-moe"
    temperature:   float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens:    int   = Field(default=4096, ge=1, le=32000)

class ProjectUpdate(BaseModel):
    name:          Optional[str]   = None
    system_prompt: Optional[str]   = None
    description:   Optional[str]   = None
    model_id:      Optional[str]   = None
    temperature:   Optional[float] = None
    max_tokens:    Optional[int]   = None

@router.post("", status_code=201)
async def create_project(
    req:          ProjectCreate,
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    project_id = "proj-" + secrets.token_urlsafe(16)
    project    = Project(
        user_id       = api_key_meta["user_id"],
        project_id    = project_id,
        name          = req.name,
        description   = req.description or "",
        system_prompt = req.system_prompt,
        model_id      = req.model_id,
        temperature   = req.temperature,
        max_tokens    = req.max_tokens
    )
    db.add(project)
    await db.commit()
    return {
        "project_id": project_id,
        "name":       req.name,
        "model_id":   req.model_id,
        "message":    "Pass project_id in chat requests to use this config."
    }

@router.get("")
async def list_projects(
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    result   = await db.execute(
        select(Project)
        .where(Project.user_id == api_key_meta["user_id"], Project.is_active == True)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return {
        "projects": [
            {
                "project_id":  p.project_id,
                "name":        p.name,
                "description": p.description,
                "model_id":    p.model_id,
                "temperature": p.temperature,
                "max_tokens":  p.max_tokens,
                "created_at":  p.created_at
            }
            for p in projects
        ]
    }

@router.get("/{project_id}")
async def get_project(
    project_id:   str,
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    result  = await db.execute(
        select(Project).where(
            Project.project_id == project_id,
            Project.user_id    == api_key_meta["user_id"],
            Project.is_active  == True
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project

@router.put("/{project_id}")
async def update_project(
    project_id:   str,
    req:          ProjectUpdate,
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    await db.execute(
        update(Project)
        .where(Project.project_id == project_id, Project.user_id == api_key_meta["user_id"])
        .values(**updates)
    )
    await db.commit()
    return {"project_id": project_id, "status": "updated"}

@router.delete("/{project_id}")
async def delete_project(
    project_id:   str,
    db:           AsyncSession = Depends(get_db),
    api_key_meta: dict = Depends(require_api_key)
):
    await db.execute(
        update(Project)
        .where(Project.project_id == project_id, Project.user_id == api_key_meta["user_id"])
        .values(is_active=False)
    )
    await db.commit()
    return {"project_id": project_id, "status": "deleted"}
