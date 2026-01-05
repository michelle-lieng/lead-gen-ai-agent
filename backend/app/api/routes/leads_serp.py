"""
Query endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Response
import openai

from ...services.leads_serp_service import leads_serp_service
from ...services.job_service import job_service
from ...exceptions import ExternalScraperError, UrlNotFoundError, DuplicateUrlError, OpenAITokenLimitExceededError, ProjectNotFoundError, InvalidProjectConfigurationError, DatabaseFailureError

logger = logging.getLogger(__name__)

from ...models.schemas import QueryListRequest, QueryGenerationRequest, UrlCreate, UrlUpdate
from fastapi import APIRouter, Response

from ...services.leads_serp_service import leads_serp_service
from ...models.schemas import (
    QueryListRequest, 
    QueryGenerationRequest, 
    QueryResponse,
    UrlCreate, 
    UrlUpdate, 
    UrlResponse,
    UrlGenerationResponse,
    LeadExtractionResponse
)

router = APIRouter()

@router.post("/projects/{project_id}/queries", response_model=list[str])
async def generate_queries(project_id: int, request: QueryGenerationRequest):
    """
    Generate AI-powered search queries for a project based on its description.
    
    Args:
        project_id: ID of the project
        request: Request body with num_queries (defaults to 3 if not provided)
    
    Returns list of generated search query strings.
    """
    return leads_serp_service.generate_queries(project_id, num_queries=request.num_queries)

@router.get("/projects/{project_id}/queries", response_model=list[QueryResponse])
async def get_queries(project_id: int):
    """
    Get all queries for a project from the database.
    
    Returns list of query objects with metadata.
    """
    return leads_serp_service.get_queries(project_id)

@router.post("/projects/{project_id}/urls", response_model=UrlGenerationResponse)
async def generate_urls(project_id: int, request: QueryListRequest):
    """
    Save queries and generate URLs for a project.
    
    Business workflow:
    1. Save generated queries to serp_queries table
    2. Generate URLs from queries and save them to serp_urls table
    
    Returns operation status and statistics.
    """
    try:
        # Check if there is a running job
        running_job = job_service.check_running_job(project_id, "generate_urls")
        if running_job:
            raise HTTPException(status_code=400, detail=f"URLs generation is already running for project {project_id}")
        
        # Create job
        job = job_service.create_job(project_id, "generate_urls")
        
        result = await leads_serp_service.save_queries_and_generate_urls(project_id, request.queries)
        
        # Update job status to completed
        job_service.mark_job_as_completed(job.id)
        
        return result
    except ProjectNotFoundError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except ExternalScraperError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        # External scraper API failed (already retried in scraper)
        raise HTTPException(status_code=502, detail=f"External scraper service error: {str(e)}")
    except DatabaseFailureError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        logger.exception(f"Database error saving queries and generating URLs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        job_service.mark_job_as_failed(job.id, str(e))
        logger.exception(f"Error saving queries and generating URLs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/projects/{project_id}/urls", response_model=list[UrlResponse])
async def get_urls(project_id: int):
    """
    Get all unprocessed production URLs for a project.
    
    Returns list of URL objects with metadata.
    """
    return leads_serp_service.get_urls(project_id)

@router.post("/projects/{project_id}/urls/create", response_model=UrlResponse)
async def create_url(project_id: int, url_data: UrlCreate):
    """
    Create a single production URL manually.
    
    Returns success status and created URL data.
    """
    return leads_serp_service.create_url(
        project_id=project_id,
        link=url_data.link,
        title=url_data.title,
        snippet=url_data.snippet,
        date=url_data.date
    )

@router.put("/projects/{project_id}/urls/{url_id}", response_model=UrlResponse)
async def update_url(project_id: int, url_id: int, update: UrlUpdate):
    """
    Update a production URL (title, snippet, date or link).
    
    Returns success status and updated URL data.
    """
    return leads_serp_service.update_url(
        project_id=project_id,
        url_id=url_id,
        title=update.title,
        snippet=update.snippet,
        link=update.link,
        date=update.date
    )

@router.delete("/projects/{project_id}/urls/{url_id}", status_code=204)
async def delete_url(project_id: int, url_id: int):
    """
    Delete a production URL.
    """
    leads_serp_service.delete_url(project_id=project_id, url_id=url_id)
    return 

@router.post("/projects/{project_id}/leads", response_model=LeadExtractionResponse)
async def generate_leads(project_id: int):
    """
    Extract leads from SERP URLs for a project.
    
    Processes unprocessed URLs, extracts leads using AI, and saves to database.
    Returns detailed extraction statistics and results.
    """
    try:
        # Check if there is a running job
        running_job = job_service.check_running_job(project_id, "leads_serp")
        if running_job:
            raise HTTPException(status_code=400, detail=f"Leads generation is already running for project {project_id}")
        
        # Create job
        job = job_service.create_job(project_id, "generate_leads")
        
        # Step 1: Save leads to serp_leads and update serp_urls
        result = await leads_serp_service.extract_and_add_leads_to_table(project_id)

        # Update job status to completed
        job_service.mark_job_as_completed(job.id)

        return result
    except ProjectNotFoundError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidProjectConfigurationError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalScraperError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        # External scraper API failed (already retried in scraper)
        raise HTTPException(status_code=502, detail=f"External scraper service error: {str(e)}")
    except OpenAITokenLimitExceededError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        # OpenAI request too large even after truncation
        raise HTTPException(status_code=413, detail=str(e))
    except openai.APIError as e:
        job_service.mark_job_as_failed(job.id, str(e))
        # All OpenAI API errors (server down, auth issues, etc.) - service layer already handles retries
        raise HTTPException(status_code=502, detail=f"OpenAI service error: {str(e)}")
    except DatabaseFailureError as e:
        logger.exception(f"Database error extracting leads: {str(e)}")
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception(f"Error extracting leads: {str(e)}")
        job_service.mark_job_as_failed(job.id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/projects/{project_id}/leads/download")
async def get_latest_run_results(project_id: int):
    """
    Get ZIP file containing all project data (queries, URLs, leads).
    
    Returns all data for the project as a ZIP file with three CSV files.
    """
    zip_bytes, filename = leads_serp_service.export_all_data_as_zip(project_id)
    
    # No data available - return 204 No Content
    if zip_bytes is None:
        return Response(status_code=204)
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
