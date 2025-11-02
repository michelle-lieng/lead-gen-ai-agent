"""
Project management endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from ...services.project_service import project_service
from ...models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    try:
        db_project = project_service.create_project(
            project_name=project.project_name,
            description=project.description
        )
        return ProjectResponse(
            id=db_project.id,
            project_name=db_project.project_name,
            description=db_project.description,
            status=db_project.status,
            date_added=db_project.date_added.isoformat(),
            last_updated=db_project.last_updated.isoformat(),
            leads_collected=db_project.leads_collected,
            datasets_added=db_project.datasets_added,
            urls_processed=db_project.urls_processed
        )
    except ValueError as e:
        # Handle duplicate project name
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

@router.get("/", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects"""
    try:
        projects = project_service.get_projects()
        return [
            ProjectResponse(
                id=p.id,
                project_name=p.project_name,
                description=p.description,
                status=p.status,
                date_added=p.date_added.isoformat(),
                last_updated=p.last_updated.isoformat(),
                leads_collected=p.leads_collected,
                datasets_added=p.datasets_added,
                urls_processed=p.urls_processed
            ) for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """Get specific project details by ID"""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        return ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            description=project.description,
            status=project.status,
            date_added=project.date_added.isoformat(),
            last_updated=project.last_updated.isoformat(),
            leads_collected=project.leads_collected,
            datasets_added=project.datasets_added,
            urls_processed=project.urls_processed
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project: {str(e)}")

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project: ProjectUpdate):
    """Update project by ID"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in project.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_project = project_service.update_project(project_id, **update_data)
        if not updated_project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        return ProjectResponse(
            id=updated_project.id,
            project_name=updated_project.project_name,
            description=updated_project.description,
            status=updated_project.status,
            date_added=updated_project.date_added.isoformat(),
            last_updated=updated_project.last_updated.isoformat(),
            leads_collected=updated_project.leads_collected,
            datasets_added=updated_project.datasets_added,
            urls_processed=updated_project.urls_processed
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """Delete project by ID"""
    try:
        success = project_service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        return {"message": f"Project {project_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")
