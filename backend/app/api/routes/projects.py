"""
Project management endpoints
"""
from fastapi import APIRouter

from ...services.project_service import project_service
from ...models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project_data: ProjectCreate):
    """Create a new project"""
    return project_service.create_project(
        project_name=project_data.project_name,
        description=project_data.description
    )

@router.get("/", response_model=list[ProjectResponse])
async def get_projects():
    """List all projects"""
    return project_service.get_projects()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """Get specific project details by ID"""
    return project_service.get_project(project_id)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_data: ProjectUpdate):
    """Update project by ID"""
    # Convert Pydantic model to dict, excluding None values
    update_data = project_data.dict(exclude_unset=True)
    return project_service.update_project(project_id, **update_data)

@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int):
    """Delete project by ID"""
    project_service.delete_project(project_id)
    return