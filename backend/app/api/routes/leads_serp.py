"""
Query endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
import asyncio

from ...services.leads_serp_service import leads_serp_service
from ...services.project_service import project_service

from ...models.schemas import QueryListRequest

router = APIRouter()

@router.post("/projects/{project_id}/leads/serp/queries")
async def generate_queries(project_id: int) -> list:
    """Gets the project id 
    -> gets description 
    -> generates queries
    -> saves them to the frontend"""
    try:
        project = project_service.get_project(project_id)
        query_list = leads_serp_service.generate_search_queries(project.description)
        return query_list
    except ValueError as e:
        # Handle project not found (ValueError from project_service.get_project)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating queries: {str(e)}")

@router.post("/projects/{project_id}/leads/serp/urls")
async def generate_urls(project_id: int, request: QueryListRequest):
    """
    For given project_id
    1. Save generated queries to serp_queries table
    2. Generate new urls and save them to serp_urls table
    """
    try:
        # Step 1: Save generated queries to serp_queries table
        step_1_success = leads_serp_service.add_queries_to_table(project_id, request.queries)

        # Step 2: Save generated urls to serp_urls table
        step_2_success = leads_serp_service.generate_and_add_urls_to_table(project_id, request.queries)
        return {"success_saved_to_serp_queries": step_1_success,
        "success_saved_to_serp_urls": step_2_success,
        "message": f"Saved and processed {len(request.queries)} queries"}
    except ValueError as e:
        # Handle specific validation errors (like foreign key violations)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving queries: {str(e)}")
