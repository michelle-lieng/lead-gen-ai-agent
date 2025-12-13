"""
Dataset management endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
import json
from ...services.leads_dataset_service import leads_dataset_service

router = APIRouter()

@router.post("/projects/{project_id}/datasets")
async def upload_dataset(
    project_id: int,
    dataset_name: str = Form(...),
    lead_column: str = Form(...),
    enrichment_column_list: str = Form(...),  # JSON-encoded list of enrichment column names
    enrichment_column_exists: bool = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload a CSV or Excel dataset for a project.
    
    Args:
        project_id: Project ID to link dataset to
        dataset_name: User-friendly name for the dataset
        lead_column: Name of column containing leads (company names)
        enrichment_column_list: JSON-encoded list of enrichment column names
        enrichment_column_exists: Whether the enrichment column exists in file
        file: CSV or Excel file to upload (.csv, .xlsx, .xls)
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")
        
        filename_lower = file.filename.lower()
        is_csv = filename_lower.endswith('.csv')
        is_excel = filename_lower.endswith(('.xlsx', '.xls'))
        
        if not (is_csv or is_excel):
            raise HTTPException(
                status_code=400, 
                detail="File must be a CSV (.csv) or Excel (.xlsx, .xls) file"
            )
        
        # Read file content as bytes
        file_content = await file.read()
        
        # Validate file is not empty
        if not file_content:
            file_type = "CSV" if is_csv else "Excel"
            raise HTTPException(status_code=400, detail=f"{file_type} file is empty")
        
        # Parse JSON-encoded enrichment_column_list string into list 
        enrichment_column_list_parsed = []
        if enrichment_column_list and enrichment_column_list.strip():
            try:
                enrichment_column_list_parsed = json.loads(enrichment_column_list)
                if not isinstance(enrichment_column_list_parsed, list):
                    raise ValueError(f"enrichment_column_list must be a JSON array, got: {type(enrichment_column_list_parsed).__name__}")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid JSON format for enrichment_column_list. Error: {str(e)}. Received: {repr(enrichment_column_list)}"
                )
        # If enrichment_column_list is empty string or '[]', enrichment_column_list_parsed will be []
        
        # Call service to process the dataset
        result = leads_dataset_service.upload_dataset(
            project_id=project_id,
            dataset_name=dataset_name,
            lead_column=lead_column,
            enrichment_column_list=enrichment_column_list_parsed,
            enrichment_column_exists=enrichment_column_exists,
            file_content=file_content,
            is_excel=is_excel
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except ValueError as e:
        # Validation errors (e.g., project not found, column not found, duplicate leads)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Validation error uploading dataset: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error uploading dataset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading dataset: {str(e)}")
