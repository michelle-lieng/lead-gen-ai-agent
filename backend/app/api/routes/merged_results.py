"""
Merged results endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Response
from ...services.merged_results_service import merged_results_service
from ...exceptions import ProjectNotFoundError, DatabaseFailureError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/projects/{project_id}/results")
async def get_merged_results(project_id: int):
    """
    Get merged results table as JSON for displaying in frontend table.
    
    Returns merged_results table as JSON with all enrichment columns (dynamically added).
    """
    result = merged_results_service.get_merged_results(project_id)
    return result

@router.get("/projects/{project_id}/results/download")
async def download_merged_results(project_id: int):
    """
    Get ZIP file containing merged results table for the project.
    
    Returns merged_results table as a ZIP file with CSV file.
    Includes all enrichment columns (dynamically added).
    Returns 204 No Content if there are no merged results to download.
    """
    zip_bytes, filename = merged_results_service.export_merged_results_as_zip(project_id)
    
    # Check if there's no data to download (returns None, None)
    if zip_bytes is None and filename is None:
        return Response(status_code=204)  # No Content
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
