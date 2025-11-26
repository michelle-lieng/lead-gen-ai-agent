"""
Test lead extraction prompts endpoints for testing lead extraction prompts
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ...services.test_lead_extraction_prompts_service import test_lead_extraction_prompts_service
from ...models.tables import TestSerpUrl
from ...models.schemas import TestQueryRequest, TestUrlUpdate
from ...services.database_service import db_service

router = APIRouter()

@router.post("/projects/{project_id}/test/urls")
async def generate_test_urls(project_id: int, request: TestQueryRequest):
    """
    Generate test URLs from a search query and save them to test_serp_urls table.
    """
    try:
        result = test_lead_extraction_prompts_service.generate_and_add_test_urls_to_table(
            project_id=project_id,
            query=request.query
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating test URLs: {str(e)}")


@router.get("/projects/{project_id}/test/urls")
async def get_test_urls(project_id: int):
    """
    Get all test URLs for a project.
    """
    try:
        with db_service.get_session() as session:
            urls = session.query(TestSerpUrl).filter(
                TestSerpUrl.project_id == project_id
            ).order_by(TestSerpUrl.created_at.desc()).all()
            
            return [
                {
                    "id": url.id,
                    "project_id": url.project_id,
                    "query": url.query,
                    "title": url.title,
                    "link": url.link,
                    "snippet": url.snippet,
                    "website_scraped": url.website_scraped,
                    "status": url.status,
                    "created_at": url.created_at.isoformat() if url.created_at else None
                }
                for url in urls
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching test URLs: {str(e)}")

@router.put("/projects/{project_id}/test/urls/{url_id}")
async def update_test_url(project_id: int, url_id: int, update: TestUrlUpdate):
    """
    Update a test URL (title, snippet, query, or status).
    """
    try:
        with db_service.get_session() as session:
            url = session.query(TestSerpUrl).filter(
                TestSerpUrl.id == url_id,
                TestSerpUrl.project_id == project_id
            ).first()
            
            if not url:
                raise HTTPException(status_code=404, detail="Test URL not found")
            
            # Update fields if provided
            if update.title is not None:
                url.title = update.title
            if update.snippet is not None:
                url.snippet = update.snippet
            if update.query is not None:
                url.query = update.query
            if update.status is not None:
                url.status = update.status
            
            session.commit()
            
            return {
                "success": True,
                "message": "Test URL updated successfully",
                "url": {
                    "id": url.id,
                    "project_id": url.project_id,
                    "query": url.query,
                    "title": url.title,
                    "link": url.link,
                    "snippet": url.snippet,
                    "status": url.status
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating test URL: {str(e)}")


@router.delete("/projects/{project_id}/test/urls/{url_id}")
async def delete_test_url(project_id: int, url_id: int):
    """
    Delete a test URL.
    """
    try:
        with db_service.get_session() as session:
            url = session.query(TestSerpUrl).filter(
                TestSerpUrl.id == url_id,
                TestSerpUrl.project_id == project_id
            ).first()
            
            if not url:
                raise HTTPException(status_code=404, detail="Test URL not found")
            
            session.delete(url)
            session.commit()
            
            return {
                "success": True,
                "message": "Test URL deleted successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting test URL: {str(e)}")


@router.post("/projects/{project_id}/test/leads")
async def extract_test_leads(project_id: int):
    """
    Extract leads from test URLs and return them (without saving to database).
    """
    try:
        result = await test_lead_extraction_prompts_service.extract_test_leads(project_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting test leads: {str(e)}")

