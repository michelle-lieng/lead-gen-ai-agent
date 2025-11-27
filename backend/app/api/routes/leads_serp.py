"""
Query endpoints
"""
from fastapi import APIRouter, HTTPException, Response

from ...services.leads_serp_service import leads_serp_service

from ...models.schemas import QueryListRequest, QueryGenerationRequest

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
    try:
        query_list = leads_serp_service.generate_search_queries_for_project(project_id, num_queries=request.num_queries)
        return query_list
    except ValueError as e:
        # Handle project not found (ValueError from service)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating queries: {str(e)}")

@router.post("/projects/{project_id}/urls")
async def generate_urls(project_id: int, request: QueryListRequest):
    """
    Save queries and generate URLs for a project.
    
    Business workflow:
    1. Save generated queries to serp_queries table
    2. Generate URLs from queries and save them to serp_urls table
    """
    try:
        result = leads_serp_service.save_queries_and_generate_urls(project_id, request.queries)
        return result
    except ValueError as e:
        # Handle specific validation errors (like foreign key violations)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving queries: {str(e)}")

@router.post("/projects/{project_id}/leads")
async def generate_leads(project_id: int):
    """
    For given project_id
    1. We load up the serp_urls and we ingest it our code will go down each row
    and if status = unprocessed then we will update that table and extract the leads
    and save to serp_leads table --> using function extract_and_add_leads_to_table
    """
    try:
        # Step 1: Save leads to serp_leads and update serp_urls
        result = await leads_serp_service.extract_and_add_leads_to_table(project_id)

        return result
    except ValueError as e:
        # Handle specific validation errors (like foreign key violations)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving queries: {str(e)}")

@router.get("/projects/{project_id}/leads/download")
async def get_latest_run_results(project_id: int):
    """
    Get ZIP file containing all project data (queries, URLs, leads).
    
    Returns all data for the project as a ZIP file with three CSV files.
    """
    try:
        zip_bytes, filename = leads_serp_service.export_all_data_as_zip(project_id)
        
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
        raise HTTPException(status_code=500, detail=f"Error downloading data: {str(e)}")
