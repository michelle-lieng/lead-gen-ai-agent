"""
Dataset management endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
import json
from ...services.leads_dataset_service import leads_dataset_service
from ...services.job_service import job_service
from ...exceptions import ProjectNotFoundError, DatabaseFailureError, InvalidFileError, InvalidEnrichmentColumnError

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
    try:
        # Check if there is a running job
        running_job = job_service.check_running_job(project_id, "leads_dataset")
        if running_job:
            raise HTTPException(status_code=400, detail=f"Dataset upload is already running for project {project_id}")
        
        # Create job
        job = job_service.create_job(project_id, "leads_dataset")
        
        # Call service to process the dataset
        result = await leads_dataset_service.upload_dataset(
            project_id=project_id,
            dataset_name=dataset_name,
            lead_column=lead_column,
            enrichment_column_list=enrichment_column_list,
            enrichment_column_exists=enrichment_column_exists,
            file=file
        )
        
        # Update job status to completed
        job_service.mark_job_as_completed(job.id)
        
        return result
        
    except ProjectNotFoundError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidFileError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidEnrichmentColumnError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseFailureError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
    except ValueError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"❌ Unexpected error uploading dataset: {e}")
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
