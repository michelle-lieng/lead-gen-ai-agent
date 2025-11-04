"""
Dataset management endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
from ...services.leads_dataset_service import leads_dataset_service

router = APIRouter()

@router.post("/projects/{project_id}/datasets/upload")
async def upload_dataset(
    project_id: int,
    dataset_name: str = Form(...),
    lead_column: str = Form(...),
    enrichment_column: str = Form(...),
    enrichment_column_exists: bool = Form(...),
    csv_file: UploadFile = File(...)
):
    """
    Upload a CSV dataset for a project.
    
    Args:
        project_id: Project ID to link dataset to
        dataset_name: User-friendly name for the dataset
        lead_column: Name of column containing leads (company names)
        enrichment_column: Name of column for enrichment values
        enrichment_column_exists: Whether the enrichment column exists in CSV
        csv_file: CSV file to upload
    """
    try:
        # Validate file type
        if not csv_file.filename or not csv_file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read file content as bytes
        csv_content = await csv_file.read()
        
        # Validate file is not empty
        if not csv_content:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Call service to process the dataset
        result = leads_dataset_service.upload_dataset(
            project_id=project_id,
            dataset_name=dataset_name,
            lead_column=lead_column,
            enrichment_column=enrichment_column,
            enrichment_column_exists=enrichment_column_exists,
            csv_content=csv_content
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except ValueError as e:
        # Validation errors (e.g., project not found, column not found)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading dataset: {str(e)}")

