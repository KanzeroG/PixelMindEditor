# ═══════════════════════════════════════════
# Gallery Router — Project CRUD
# ═══════════════════════════════════════════

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import get_current_user_id
from models.schemas import ProjectCreate, ProjectResponse

router = APIRouter()

# In-memory gallery store
projects_db: dict[str, dict] = {}


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(user_id: str = Depends(get_current_user_id)):
    user_projects = [
        ProjectResponse(
            id=p["id"],
            title=p["title"],
            image_url=p.get("image_url"),
            result_url=p.get("result_url"),
            tool_used=p.get("tool_used"),
            prompt=p.get("prompt"),
            is_public=p.get("is_public", False),
            created_at=p["created_at"],
        )
        for p in projects_db.values()
        if p["user_id"] == user_id
    ]
    return sorted(user_projects, key=lambda x: x.created_at, reverse=True)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    user_id: str = Depends(get_current_user_id),
):
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "user_id": user_id,
        "title": data.title,
        "image_url": data.image_url,
        "result_url": data.result_url,
        "tool_used": data.tool_used,
        "prompt": data.prompt,
        "is_public": False,
        "created_at": datetime.now(timezone.utc),
    }
    projects_db[project_id] = project

    return ProjectResponse(
        id=project_id,
        title=data.title,
        image_url=data.image_url,
        result_url=data.result_url,
        tool_used=data.tool_used,
        prompt=data.prompt,
        is_public=False,
        created_at=project["created_at"],
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
):
    project = projects_db.get(project_id)
    if not project or project["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Project not found")

    del projects_db[project_id]
    return {"message": "Project deleted"}
