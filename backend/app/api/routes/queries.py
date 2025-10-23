"""
Query endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from ...services.leads_from_search import generate_search_queries
from .projects import get_project
import asyncio

router = APIRouter()

@router.post("/projects/{project_id}/generate_queries")
async def generate_queries(project_id):
    """Create a new project"""
    try:
        project_response = await get_project(project_id)
        project_description = project_response.description
        query_list = generate_search_queries(project_description)
        return query_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")
