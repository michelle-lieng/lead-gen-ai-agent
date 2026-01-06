"""
Job status API client
"""

from typing import Optional
from .base import _request
from urllib.parse import urlencode


def get_job_status(
    project_id: int, job_type: str, job_type_id: Optional[int] = None
) -> Optional[dict]:
    """
    Get the status of the most recent job for a project and job type.

    Args:
        project_id: ID of the project
        job_type: Type of job (e.g., "enrichments", "generate_urls", "generate_leads")
        job_type_id: Optional ID for job type (e.g., enrichment_id for "enrichments")

    Returns:
        Dict with job status ("running", "completed", or "failed") if job exists, None if no job found
    """
    path = f"/api/projects/{project_id}/jobs/{job_type}"
    
    # Build query string if job_type_id is provided
    if job_type_id is not None:
        query_string = urlencode({"job_type_id": job_type_id})
        path = f"{path}?{query_string}"

    response = _request("GET", path)
    
    # Handle case where no job exists (returns None/204)
    if response.status_code == 204 or not response.content:
        return None
    
    return response.json()
