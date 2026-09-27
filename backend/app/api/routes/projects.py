"""
Project management endpoints
"""
import logging

from fastapi import APIRouter, Depends

from ..deps import ApiKeys, get_api_keys
from ...exceptions import AppError
from ...services.agent_brief_service import agent_brief_service
from ...services.project_service import project_service
from ...models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(project_data: ProjectCreate, keys: ApiKeys = Depends(get_api_keys)):
    """
    Create a new project, with example first messages written for it from its
    title and description when an OpenAI key is supplied. The project is
    created either way; without examples the chat shows generic ones until
    POST /{project_id}/example-prompts writes them.
    """
    project = project_service.create_project(
        project_name=project_data.project_name,
        description=project_data.description
    )
    if keys.openai_api_key and keys.openai_api_key.strip():
        try:
            prompts = agent_brief_service.draft_example_prompts(
                project.project_name,
                project.description,
                openai_api_key=keys.openai_api_key.strip(),
            )
            if prompts:
                project = project_service.set_example_prompts(project.id, prompts)
        except AppError:
            logger.warning(f"Example prompts not written for project {project.id}", exc_info=True)
    return project

@router.post("/{project_id}/example-prompts", response_model=ProjectResponse)
def write_example_prompts(project_id: int, keys: ApiKeys = Depends(get_api_keys)):
    """Write (or rewrite) a project's example first messages from its title and description."""
    project = project_service.get_project(project_id)
    prompts = agent_brief_service.draft_example_prompts(
        project.project_name, project.description, openai_api_key=keys.require_openai()
    )
    return project_service.set_example_prompts(project_id, prompts)

@router.get("/", response_model=list[ProjectResponse])
def get_projects():
    """List all projects"""
    return project_service.get_projects()

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    """Get specific project details by ID"""
    return project_service.get_project(project_id)

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_data: ProjectUpdate):
    """Update project by ID"""
    # Convert Pydantic model to dict, excluding None values
    update_data = project_data.dict(exclude_unset=True)
    return project_service.update_project(project_id, **update_data)

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int):
    """Delete project by ID"""
    project_service.delete_project(project_id)
    return