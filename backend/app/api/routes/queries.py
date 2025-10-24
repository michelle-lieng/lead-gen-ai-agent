"""
Query endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from ...services.leads_from_search import GenerateLeadsFromSearch
from ...models.schemas import QueryListRequest
from .projects import get_project
import asyncio

router = APIRouter()
leads_from_search = GenerateLeadsFromSearch()

@router.post("/projects/{project_id}/leads/generate_queries")
async def generate_queries(project_id: int) -> list:
    """Create a new project"""
    try:
        project_response = await get_project(project_id)
        query_list = leads_from_search.generate_search_queries(project_response.description)
        return query_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

@router.post("/projects/{project_id}/leads/generate_urls")
async def generate_urls(project_id: int, request: QueryListRequest):
    """Save generated queries to the database for a project"""
    try:
        success = leads_from_search.add_queries_to_table(project_id, request.queries)
        return {"success": success, "message": f"Saved {len(request.queries)} queries to database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving queries: {str(e)}")
