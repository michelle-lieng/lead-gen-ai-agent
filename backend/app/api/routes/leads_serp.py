"""
Query endpoints
"""
from fastapi import APIRouter, HTTPException, Response
from typing import List
import asyncio
from datetime import datetime
import re
import zipfile
from io import BytesIO


from ...services.leads_serp_service import leads_serp_service
from ...services.project_service import project_service

from ...models.schemas import QueryListRequest

router = APIRouter()

@router.post("/projects/{project_id}/leads/serp/queries")
async def generate_queries(project_id: int) -> list:
    """
    Generate AI-powered search queries for a project based on its description.
    
    Gets the project id -> service handles fetching description and generating queries
    """
    try:
        query_list = leads_serp_service.generate_search_queries_for_project(project_id)
        return query_list
    except ValueError as e:
        # Handle project not found (ValueError from service)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating queries: {str(e)}")

@router.post("/projects/{project_id}/leads/serp/urls")
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

@router.post("/projects/{project_id}/leads/serp/results")
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

@router.get("/projects/{project_id}/leads/serp/results")
async def get_latest_run_results(project_id: int):
    """
    Get ZIP file containing all project data (queries, URLs, leads).
    
    Returns all data for the project as a ZIP file with three CSV files.
    """
    try:
        # Export all CSV files for the project (no filtering)
        export_result = leads_serp_service.export_all_data_as_csv(project_id)
        
        csv_files = export_result.get("csv_files", {})
        
        if not csv_files:
            raise HTTPException(status_code=404, detail="No data found for this project")
        
        # Always return ZIP file with all tables
        # Use current timestamp for filename
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get project name for meaningful filename
        project_name = project_service.get_project(project_id).project_name
        # Sanitize project name for filename (remove special chars, replace spaces with underscores)
        safe_project_name = re.sub(r'[^\w\s-]', '', project_name).strip().replace(' ', '_')
        
        zip_filename = f"{safe_project_name}_serp_lead_gen_{timestamp_str}.zip"
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for name, csv_content in csv_files.items():
                zip_file.writestr(f"serp_{name}.csv", csv_content.encode('utf-8-sig'))
        
        zip_buffer.seek(0)
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading CSV: {str(e)}")
