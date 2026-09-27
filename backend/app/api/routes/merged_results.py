"""
Merged results endpoints
"""
from fastapi import APIRouter, Query, Response
from ...services.merged_results_service import merged_results_service
from ...models.schemas import MergedResultsResponse, MergedRowUpdate

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

@router.patch("/projects/{project_id}/results/row", response_model=dict)
async def update_merged_row(project_id: int, request: MergedRowUpdate):
    """
    Edit one entry in the merged results table.

    The row is addressed by its current lead name. Editable columns are the
    lead name itself and the project's enrichment columns; `serp_count` is
    derived from the SERP aggregation and is read-only.
    """
    return merged_results_service.update_merged_row(
        project_id, request.lead, request.updates
    )

@router.delete("/projects/{project_id}/results/row", status_code=204)
async def delete_merged_row(
    project_id: int,
    lead: str = Query(..., description="Lead name identifying the row to delete"),
):
    """
    Remove one entry from the merged results table.
    """
    merged_results_service.delete_merged_row(project_id, lead)
    return
