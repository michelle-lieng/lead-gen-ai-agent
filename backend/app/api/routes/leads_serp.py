"""
Query endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Response
import openai

from ...services.leads_serp_service import leads_serp_service
from ...exceptions import ExternalScraperError, UrlNotFoundError, DuplicateUrlError, OpenAITokenLimitExceededError, ProjectNotFoundError, InvalidProjectConfigurationError, DatabaseFailureError

logger = logging.getLogger(__name__)

from ...models.schemas import QueryListRequest, QueryGenerationRequest, UrlCreate, UrlUpdate

router = APIRouter()

@router.post("/projects/{project_id}/queries")
async def generate_queries(
    project_id: int,
    request: QueryGenerationRequest
) -> list:
    """
    Generate AI-powered search queries for a project based on its description.
    
    Args:
        project_id: ID of the project
        request: Request body with num_queries (defaults to 3 if not provided)
    
    Gets the project id -> service handles fetching description and generating queries
    """
    query_list = leads_serp_service.generate_search_queries_for_project(project_id, num_queries=request.num_queries)
    return query_list

@router.get("/projects/{project_id}/queries")
async def get_queries(project_id: int):
    """
    Get all queries for a project from the database.
    """
    queries = leads_serp_service.get_queries(project_id)
    return queries

@router.post("/projects/{project_id}/urls")
async def generate_urls(project_id: int, request: QueryListRequest):
    """
    Save queries and generate URLs for a project.
    
    Business workflow:
    1. Save generated queries to serp_queries table
    2. Generate URLs from queries and save them to serp_urls table
    """
    result = await leads_serp_service.save_queries_and_generate_urls(project_id, request.queries)
    return result

@router.get("/projects/{project_id}/urls")
async def get_urls(project_id: int):
    """
    Get all production URLs for a project.
    """
    urls = leads_serp_service.get_urls(project_id)
    return urls

@router.post("/projects/{project_id}/urls/create")
async def create_url(project_id: int, url_data: UrlCreate):
    """
    Create a single production URL manually.
    """
    result = leads_serp_service.create_url(
        project_id=project_id,
        link=url_data.link,
        title=url_data.title,
        snippet=url_data.snippet,
        date=url_data.date
    )
    return result

@router.put("/projects/{project_id}/urls/{url_id}")
async def update_url(project_id: int, url_id: int, update: UrlUpdate):
    """
    Update a production URL (title, snippet, date or link).
    """
    result = leads_serp_service.update_url(
        project_id=project_id,
        url_id=url_id,
        title=update.title,
        snippet=update.snippet,
        link=update.link,
        date=update.date
    )
    return result

@router.delete("/projects/{project_id}/urls/{url_id}")
async def delete_url(project_id: int, url_id: int):
    """
    Delete a production URL.
    """
    result = leads_serp_service.delete_url(project_id=project_id, url_id=url_id)
    return result

@router.post("/projects/{project_id}/leads")
async def generate_leads(project_id: int):
    """
    For given project_id
    1. We load up the serp_urls and we ingest it our code will go down each row
    and if status = unprocessed then we will update that table and extract the leads
    and save to serp_leads table --> using function extract_and_add_leads_to_table
    """
    # Step 1: Save leads to serp_leads and update serp_urls
    result = await leads_serp_service.extract_and_add_leads_to_table(project_id)
    return result

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
