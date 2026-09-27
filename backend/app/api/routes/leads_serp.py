"""
Query endpoints
"""
import logging
from fastapi import APIRouter, Depends, Response
import openai

from ...services.leads_serp_service import leads_serp_service
from ...services.job_service import job_service
from ..deps import ApiKeys, get_api_keys

logger = logging.getLogger(__name__)

from ...models.schemas import QueryListRequest, QueryGenerationRequest, UrlCreate, UrlUpdate
from fastapi import APIRouter, Response

from ...services.agent_brief_service import agent_brief_service
from ...services.places_service import places_query, save_places, search_places
from ...services.project_service import project_service
from ...services.leads_serp_service import leads_serp_service
from ...models.schemas import (
    QueryListRequest,
    QueryGenerationRequest,
    QueryResponse,
    UrlCreate,
    UrlUpdate,
    UrlResponse,
    UrlGenerationResponse,
    LeadExtractionResponse,
    InstructionRequest,
    LeadBriefResponse,
    PlacesSearchRequest,
    PlacesSearchResponse,
)

router = APIRouter()

@router.post("/projects/{project_id}/lead-brief", response_model=LeadBriefResponse)
async def draft_lead_brief(
    project_id: int,
    request: InstructionRequest,
    keys: ApiKeys = Depends(get_api_keys),
):
    """
    Expand one plain-English instruction into the project's search configuration.

    The caller sends something like "dental clinics in Sydney" and gets back
    the search target, the minimum criteria a name must meet to count as a
    lead, and how many queries this target deserves. Both fields are saved to
    the project, so query generation can run immediately afterwards.
    """
    return agent_brief_service.draft_lead_brief(
        project_id,
        request.instruction,
        openai_api_key=keys.require_openai(),
    )

@router.post("/projects/{project_id}/queries", response_model=list[str])
async def generate_queries(
    project_id: int,
    request: QueryGenerationRequest,
    keys: ApiKeys = Depends(get_api_keys),
):
    """
    Generate AI-powered search queries for a project based on its description.

    Args:
        project_id: ID of the project
        request: Request body with num_queries (defaults to 3 if not provided)

    Returns list of generated search query strings.
    """
    return leads_serp_service.generate_queries(
        project_id,
        num_queries=request.num_queries,
        openai_api_key=keys.require_openai(),
    )

@router.get("/projects/{project_id}/queries", response_model=list[QueryResponse])
async def get_queries(project_id: int):
    """
    Get all queries for a project from the database.
    
    Returns list of query objects with metadata.
    """
    return leads_serp_service.get_queries(project_id)

@router.post("/projects/{project_id}/urls", response_model=UrlGenerationResponse)
async def generate_urls(
    project_id: int,
    request: QueryListRequest,
    keys: ApiKeys = Depends(get_api_keys),
):
    """
    Save queries and generate URLs for a project.

    Business workflow:
    1. Save generated queries to serp_queries table
    2. Generate URLs from queries and save them to serp_urls table

    Returns operation status and statistics.
    """
    return await leads_serp_service.generate_urls(
        project_id, request.queries, jina_api_key=keys.require_jina()
    )

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
async def generate_leads(project_id: int, keys: ApiKeys = Depends(get_api_keys)):
    """
    Extract leads from SERP URLs for a project.

    Processes unprocessed URLs, extracts leads using AI, and saves to database.
    Returns detailed extraction statistics and results.
    """
    return await leads_serp_service.generate_leads(
        project_id,
        openai_api_key=keys.require_openai(),
        jina_api_key=keys.require_jina(),
    )

@router.post("/projects/{project_id}/places", response_model=PlacesSearchResponse)
async def search_google_places(
    project_id: int,
    request: PlacesSearchRequest,
    keys: ApiKeys = Depends(get_api_keys),
):
    """
    Find businesses for a location search on Google Places and add them to the
    table as leads, with their address. Runs before the web search when a chat
    message names a place.
    """
    google_key = keys.require_google()
    project_service.get_project(project_id)  # raises if the project is gone
    query = places_query(request.query, request.location)
    places = await search_places(query, google_key)
    return save_places(project_id, query, places)

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
