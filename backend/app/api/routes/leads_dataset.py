"""
Dataset management endpoints
"""
import logging
from fastapi import APIRouter, UploadFile, File, Form
from ...services.leads_dataset_service import leads_dataset_service
from ...services.job_service import job_service

logger = logging.getLogger(__name__)

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
    # Call service to process the dataset
    result = await leads_dataset_service.upload_dataset(
        project_id=project_id,
        dataset_name=dataset_name,
        lead_column=lead_column,
        enrichment_column_list=enrichment_column_list,
        enrichment_column_exists=enrichment_column_exists,
        file=file
    )
    
    return result