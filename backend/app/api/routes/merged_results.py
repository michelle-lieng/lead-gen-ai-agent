"""
Merged results endpoints
"""
from fastapi import APIRouter, Response
from ...services.merged_results_service import merged_results_service
from ...models.schemas import MergedResultsResponse

router = APIRouter()

@router.get("/projects/{project_id}/results", response_model=MergedResultsResponse)
async def get_merged_results(project_id: int):
    """
    Get merged results table as JSON for displaying in frontend table.
    
    Returns merged_results table as JSON with all enrichment columns (dynamically added).
    """
    return merged_results_service.get_merged_results(project_id)

@router.get("/projects/{project_id}/results/download")
async def download_merged_results(project_id: int):
    """
    Get ZIP file containing merged results table for the project.
    
    Returns merged_results table as a ZIP file with CSV file.
    Includes all enrichment columns (dynamically added).
    Returns 204 No Content if there are no merged results to download.
    """
    zip_bytes, filename = merged_results_service.export_merged_results_as_zip(project_id)
    
    # Check if there's no data to download
    if zip_bytes is None:
        return Response(status_code=204)  # No Content
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
