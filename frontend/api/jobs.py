"""
Job status API client
"""

from typing import Optional
from .base import _request


def get_job_status(
    project_id: int, job_type: str, job_type_id: Optional[int] = None
) -> Optional[dict]:
    """
    Get the status of the most recent job for a project and job type.

    Args:
        project_id: ID of the project
        job_type: Type of job (e.g., "enrich_leads", "generate_urls", "generate_leads")
        job_type_id: Optional ID for job type (e.g., enrichment_id for "enrich_leads")

    Returns:
        Dict with job status ("running", "completed", or "failed") if job exists, None if no job found
    """
    params = {}
    if job_type_id is not None:
        params["job_type_id"] = job_type_id

    response = _request(
        "GET", f"/api/projects/{project_id}/jobs/{job_type}", params=params
    )

    return response
