"""
Project management endpoints
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import List
from ...services.project_service import project_service
from ...models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from ...exceptions import DuplicateProjectNameError, ProjectNotFoundError, InvalidProjectConfigurationError, DatabaseFailureError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate):
    """Create a new project"""
    try:
        project = project_service.create_project(
            project_name=project_data.project_name,
            description=project_data.description
        )
        return ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            description=project.description,
            query_search_target=project.query_search_target,
            lead_minimum_criteria=project.lead_minimum_criteria,
            date_added=project.date_added.isoformat(),
            last_updated=project.last_updated.isoformat(),
            leads_collected=project.leads_collected,
            datasets_added=project.datasets_added,
            urls_processed=project.urls_processed
        )
    except DuplicateProjectNameError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"❌ Unexpected error creating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects"""
    try:
        projects = project_service.get_projects()
        return [
            ProjectResponse(
                id=project.id,
                project_name=project.project_name,
                description=project.description,
                query_search_target=project.query_search_target,
                lead_minimum_criteria=project.lead_minimum_criteria,
                date_added=project.date_added.isoformat(),
                last_updated=project.last_updated.isoformat(),
                leads_collected=project.leads_collected,
                datasets_added=project.datasets_added,
                urls_processed=project.urls_processed
            ) for project in projects
        ]
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """Get specific project details by ID"""
    try:
        project = project_service.get_project(project_id)
        return ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            description=project.description,
            query_search_target=project.query_search_target,
            lead_minimum_criteria=project.lead_minimum_criteria,
            date_added=project.date_added.isoformat(),
            last_updated=project.last_updated.isoformat(),
            leads_collected=project.leads_collected,
            datasets_added=project.datasets_added,
            urls_processed=project.urls_processed
        )
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_data: ProjectUpdate):
    """Update project by ID"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in project_data.dict().items() if v is not None}
        project = project_service.update_project(project_id, **update_data)
        
        return ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            description=project.description,
            query_search_target=project.query_search_target,
            lead_minimum_criteria=project.lead_minimum_criteria,
            date_added=project.date_added.isoformat(),
            last_updated=project.last_updated.isoformat(),
            leads_collected=project.leads_collected,
            datasets_added=project.datasets_added,
            urls_processed=project.urls_processed
        )
    except DuplicateProjectNameError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidProjectConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"❌ Unexpected error updating project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """Delete project by ID"""
    try:
        project_service.delete_project(project_id)
        return {"message": f"Project {project_id} deleted successfully"}
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"❌ Unexpected error deleting project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
