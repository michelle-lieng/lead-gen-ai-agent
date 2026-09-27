"""
Job status endpoints
"""
import logging
from typing import Optional
from fastapi import APIRouter
from ...services.job_service import job_service
from ...models.schemas import JobResponse
from ...exceptions import ProjectNotFoundError
from ...services.project_service import project_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/projects/{project_id}/jobs/{job_type}", response_model=Optional[JobResponse])
def get_job_status(project_id: int, job_type: str, job_type_id: Optional[int] = None):
    """
    Get the status of the most recent job for a project and job type.
    
    Args:
        project_id: ID of the project
        job_type: Type of job (e.g., "enrich_leads", "generate_urls", "generate_leads")
        job_type_id: Optional ID for job type (e.g., enrichment_id for "enrich_leads")
    
    Returns:
        JobResponse with status ("running", "completed", or "failed") if job exists, None if no job found
    """
    # Verify project exists
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    
    # Get the most recent job for this project and job type (regardless of status)
    latest_job = job_service.get_latest_job(project_id, job_type, job_type_id)
    
    if latest_job:
        return JobResponse(
            id=latest_job.id,
            project_id=latest_job.project_id,
            job_type=latest_job.job_type,
            job_type_id=latest_job.job_type_id,
            status=latest_job.status,
            completed_at=latest_job.completed_at.isoformat() if latest_job.completed_at else None,
            error_message=latest_job.error_message,
        )
    
    # No job found
    return None

