"""
Merged results endpoints
"""
from fastapi import APIRouter, HTTPException, Response
from ...services.merged_results_service import merged_results_service

router = APIRouter()

@router.get("/projects/{project_id}/results")
async def get_merged_results(project_id: int):
    """
    Get merged results table as JSON for displaying in frontend table.
    
    Returns merged_results table as JSON with all enrichment columns (dynamically added).
    """
    try:
        result = merged_results_service.get_merged_results(project_id)
        return result
        
    except ValueError as e:
        # Handle "no data" or "project not found" errors
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting merged results: {str(e)}")

@router.get("/projects/{project_id}/results/download")
async def download_merged_results(project_id: int):
    """
    Get ZIP file containing merged results table for the project.
    
    Returns merged_results table as a ZIP file with CSV file.
    Includes all enrichment columns (dynamically added).
    """
    try:
        zip_bytes, filename = merged_results_service.export_merged_results_as_zip(project_id)
        
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        # Handle "no data" or "project not found" errors
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading merged results: {str(e)}")

