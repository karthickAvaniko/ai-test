from fastapi import APIRouter, Depends, HTTPException
from auth import require_api_key
from database import create_project, get_project, list_projects, update_project, delete_project
from models import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/v1/projects", tags=["Projects"])

@router.post("", status_code=201)
async def create(req: ProjectCreate, user: dict = Depends(require_api_key)):
    project_id = create_project(
        api_key=user["api_key"],
        name=req.name,
        system_prompt=req.system_prompt,
        description=req.description or "",
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )
    return {
        "project_id": project_id,
        "name": req.name,
        "model": req.model,
        "message": "Project created. Pass project_id in chat requests to use this config."
    }

@router.get("")
async def list_all(user: dict = Depends(require_api_key)):
    projects = list_projects(user["api_key"])
    return {"projects": projects, "total": len(projects)}

@router.get("/{project_id}")
async def get_one(project_id: str, user: dict = Depends(require_api_key)):
    project = get_project(project_id, user["api_key"])
    if not project:
        raise HTTPException(404, "Project not found")
    return project

@router.put("/{project_id}")
async def update(project_id: str, req: ProjectUpdate, user: dict = Depends(require_api_key)):
    if not get_project(project_id, user["api_key"]):
        raise HTTPException(404, "Project not found")
    update_project(project_id, user["api_key"], **req.model_dump())
    return {"project_id": project_id, "status": "updated"}

@router.delete("/{project_id}")
async def delete(project_id: str, user: dict = Depends(require_api_key)):
    if not get_project(project_id, user["api_key"]):
        raise HTTPException(404, "Project not found")
    delete_project(project_id, user["api_key"])
    return {"project_id": project_id, "status": "deleted"}
