"""
API client for communicating with FastAPI backend
"""

import os
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

# Configuration
# Read from environment variable (set by Docker) or default to localhost for local dev
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# Default timeout: 10 minutes (600 secs) for lead extraction operations which can process many URLs sequentially
# Each URL can take 10-30 seconds with AI processing + scraping, so with 50 URLs this could take 8+ minutes
TIMEOUT = 600

# Create one shared session for connection reuse
_session = requests.Session()

# Add retry logic
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=(502, 503, 504),
    allowed_methods=("GET", "POST", "PUT", "DELETE"),
    raise_on_status=False,
)
adapter = HTTPAdapter(max_retries=retry)
_session.mount("http://", adapter)
_session.mount("https://", adapter)
_session.headers.update({"Accept": "application/json"})

def _request(method: str, path: str, json_data=None, stream=False, files=None, form_data=None):
    """Make HTTP request - returns response or None on error"""
    try:
        # Build full URL (BASE_URL already has no trailing slash, path has leading slash)
        url = f"{BASE_URL}{path}"
        # Use files+form_data for multipart/form-data, otherwise use json_data
        if files is not None:
            response = _session.request(
                method, url, files=files, data=form_data, timeout=TIMEOUT, stream=stream
            )
        else:
            response = _session.request(
                method, url, json=json_data, timeout=TIMEOUT, stream=stream
            )
        
        return response
        # Return response even on error so we can access error details
        return response
    except Exception:
        return None

# Project endpoints
def get_projects():
    """Fetch all projects from the API"""
    response = _request("GET", "/api/projects/")
    return response.json() if response else []

def create_project(project_name: str, description: Optional[str]=None):
    """Create a new project via API"""
    response = _request("POST", "/api/projects/", json_data={
        "project_name": project_name,
        "description": description
    })
    return response.json() if response else None

def update_project(project_id: int, **kwargs):
    """Update project via API"""
    data = {k: v for k, v in kwargs.items() if v is not None}
    response = _request("PUT", f"/api/projects/{project_id}", json_data=data)
    return response.json() if response else None

def get_project(project_id: int):
    """Get specific project by ID"""
    response = _request("GET", f"/api/projects/{project_id}")
    return response.json() if response else None

def delete_project(project_id: int):
    """Delete project via API"""
    response = _request("DELETE", f"/api/projects/{project_id}")
    return response is not None

# Lead generation endpoints
def get_queries(project_id: int):
    """
    Get all queries for a project from the database via API
    
    Args:
        project_id: ID of the project
    """
    response = _request("GET", f"/api/projects/{project_id}/queries")
    return response.json() if response else None

def generate_queries(project_id: int, num_queries: int = 3):
    """
    Generate search queries for a project via API
    
    Args:
        project_id: ID of the project
        num_queries: Number of queries to generate (1-20, default: 3)
    """
    response = _request("POST", f"/api/projects/{project_id}/queries", json_data={"num_queries": num_queries})
    return response.json() if response else None

def generate_urls(project_id: int, queries: list[str]):
    """Generate URLs from search queries and save them"""
    response = _request("POST", f"/api/projects/{project_id}/urls", json_data={"queries": queries})
    return response.json() if response else None

def get_urls(project_id: int):
    """Get all production URLs for a project"""
    response = _request("GET", f"/api/projects/{project_id}/urls")
    return response.json() if response else []

def create_url(project_id: int, link: str, title: str = None, snippet: str = None, date: str = None):
    """Create a new production URL (query is automatically set to 'Manual Entry' in the backend)"""
    data = {
        "link": link
    }
    if title is not None:
        data["title"] = title
    if snippet is not None:
        data["snippet"] = snippet
    if date is not None:
        data["date"] = date
    # Note: query is automatically set to "Manual Entry" in the backend
    
    response = _request("POST", f"/api/projects/{project_id}/urls/create", json_data=data)
    return response.json() if response else None

def update_url(project_id: int, url_id: int, title: str = None, snippet: str = None, link: str = None, date: str = None):
    """Update a production URL"""
    data = {}
    if title is not None:
        data["title"] = title
    if snippet is not None:
        data["snippet"] = snippet
    if link is not None:
        data["link"] = link
    if date is not None:
        data["date"] = date
    
    response = _request("PUT", f"/api/projects/{project_id}/urls/{url_id}", json_data=data)
    return response.json() if response else None

def delete_url(project_id: int, url_id: int):
    """Delete a production URL"""
    response = _request("DELETE", f"/api/projects/{project_id}/urls/{url_id}")
    return response.json() if response else None

def generate_leads(project_id: int):
    """Extract leads from URLs and save them"""
    response = _request("POST", f"/api/projects/{project_id}/leads")
    return response.json() if response else None

def fetch_latest_run_zip(project_id: int):
    """
    Fetch ZIP file containing latest run results.
    Returns (zip_content: bytes, filename: str) or (None, None) on error
    """
    response = _request("GET", f"/api/projects/{project_id}/leads/download", stream=True)
    
    if response:
        # Get filename from Content-Disposition header (backend sets it)
        cd = response.headers.get("Content-Disposition", "")
        # Extract filename from header (format: "attachment; filename=name.zip")
        filename = cd.split("filename=", 1)[1].strip().strip('"').strip("'")
        
        return response.content, filename
    
    return None, None

# Dataset endpoints
def upload_dataset(project_id: int, dataset_name: str, lead_column: str, enrichment_column_list: list[str], enrichment_column_exists: bool, file):
    """Upload a CSV or Excel dataset for a project via API"""
    file.seek(0)
    file_content = file.read()
    file.seek(0)
    
    # Determine MIME type based on file extension
    filename_lower = file.name.lower()
    if filename_lower.endswith('.xlsx'):
        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif filename_lower.endswith('.xls'):
        mime_type = 'application/vnd.ms-excel'
    else:
        mime_type = 'text/csv'
    
    files = {'file': (file.name, file_content, mime_type)}
    form_data = {
        'dataset_name': dataset_name,
        'lead_column': lead_column,
        'enrichment_column_list': json.dumps(enrichment_column_list) if enrichment_column_list else '[]',  # Always send a JSON string, even if empty
        'enrichment_column_exists': 'true' if enrichment_column_exists else 'false'
    }
    
    response = _request("POST", f"/api/projects/{project_id}/datasets", files=files, form_data=form_data)
    if response:
        try:
            result = response.json()
            # If status code indicates error, ensure success is False
            if response.status_code >= 400:
                if 'success' not in result:
                    result['success'] = False
            return result
        except:
            # If response is not JSON, return error dict with status code
            return {"success": False, "detail": f"Server error: {response.status_code} - {response.text[:200]}"}
    return {"success": False, "detail": "No response from server"}


# Merged results endpoints
def get_merged_results(project_id: int):
    """Get merged results table as JSON for displaying in frontend"""
    response = _request("GET", f"/api/projects/{project_id}/results")
    return response.json() if response else None

def fetch_merged_results_zip(project_id: int):
    """
    Fetch ZIP file containing merged results table.
    Returns (zip_content: bytes, filename: str) or (None, None) on error
    """
    response = _request("GET", f"/api/projects/{project_id}/results/download", stream=True)
    
    if response:
        # Get filename from Content-Disposition header (backend sets it)
        cd = response.headers.get("Content-Disposition", "")
        # Extract filename from header (format: "attachment; filename=name.zip")
        filename = cd.split("filename=", 1)[1].strip().strip('"').strip("'")
        
        return response.content, filename
    
    return None, None

# Enrichment endpoints
def create_enrichment(project_id: int, enrichment_name: str, enrichment_description: Optional[str]=None):
    """Create a new enrichment via API"""
    response = _request("POST", f"/api/projects/{project_id}/enrichments/", json_data={
        "enrichment_name": enrichment_name,
        "enrichment_description": enrichment_description
    })
    return response.json() if response else None

def get_enrichments(project_id: int):
    """Get all enrichments for a project from the API"""
    response = _request("GET", f"/api/projects/{project_id}/enrichments/")
    return response.json() if response else []

def get_enrichment(enrichment_id: int):
    """Get a specific enrichment by ID from the API"""
    response = _request("GET", f"/api/enrichments/{enrichment_id}")
    return response.json() if response else None

def update_enrichment(
    enrichment_id: int,
    enrichment_name: Optional[str]=None,
    column_name: Optional[str]=None,
    enrichment_description: Optional[str]=None,
    goal: Optional[str]=None,
    acceptable_evidence: Optional[str]=None,
    result_format: Optional[str]=None,
    result_true_if: Optional[str]=None,
    result_false_if: Optional[str]=None,
    result_number_value: Optional[str]=None,
    result_text_value: Optional[str]=None
):
    """Update an enrichment via API - all fields are optional"""
    data = {}
    if enrichment_name is not None:
        data["enrichment_name"] = enrichment_name
    if column_name is not None:
        data["column_name"] = column_name
    if enrichment_description is not None:
        data["enrichment_description"] = enrichment_description
    if goal is not None:
        data["goal"] = goal
    if acceptable_evidence is not None:
        data["acceptable_evidence"] = acceptable_evidence
    if result_format is not None:
        data["result_format"] = result_format
    if result_true_if is not None:
        data["result_true_if"] = result_true_if
    if result_false_if is not None:
        data["result_false_if"] = result_false_if
    if result_number_value is not None:
        data["result_number_value"] = result_number_value
    if result_text_value is not None:
        data["result_text_value"] = result_text_value
    
    response = _request("PUT", f"/api/enrichments/{enrichment_id}", json_data=data)
    return response.json() if response else None

def delete_enrichment(enrichment_id: int):
    """Delete an enrichment via API"""
    response = _request("DELETE", f"/api/enrichments/{enrichment_id}")
    return response is not None

def enrich_leads(project_id: int, enrichment_id: int, leads_data: list, column_name: str, result_format: str):
    """Run enrichment on leads and add enrichment column via API
    
    Args:
        project_id: Project ID
        enrichment_id: Enrichment ID
        leads_data: List of lead dictionaries
        column_name: Column name for enrichment results
        result_format: Result format (True/False, Text, or Number)
    """
    if not column_name:
        return {
            "success": False,
            "message": "Column name is required to add enrichment column.",
            "leads_processed": 0,
            "enrichment_id": enrichment_id,
            "project_id": project_id
        }
    
    if not result_format:
        return {
            "success": False,
            "message": "Result format must be set before running enrichment.",
            "leads_processed": 0,
            "enrichment_id": enrichment_id,
            "project_id": project_id
        }
    
    response = _request("POST", f"/api/projects/{project_id}/enrichments/{enrichment_id}/enrich-leads", json_data={
        "enrichment_id": enrichment_id,
        "column_name": column_name,
        "result_format": result_format,
        "leads_data": leads_data
    })
    if response:
        return response.json()
    return None

def test_enrich_leads(project_id: int, enrichment_id: int, leads_data: list, column_name: str, result_format: str):
    """Run test enrichment on leads and add enrichment column via API"""
    if not column_name:
        return {
            "success": False,
            "message": "Column name is required to add enrichment column.",
            "leads_processed": 0,
            "enrichment_id": enrichment_id,
            "project_id": project_id
        }
    
    if not result_format:
        return {
            "success": False,
            "message": "Result format must be set before running enrichment.",
            "leads_processed": 0,
            "enrichment_id": enrichment_id,
            "project_id": project_id
        }
    
    try:
        response = _request("POST", f"/api/projects/{project_id}/enrichments/{enrichment_id}/test-enrich-leads", json_data={
            "enrichment_id": enrichment_id,
            "column_name": column_name,
            "result_format": result_format,
            "leads_data": leads_data
        })
        
        if response is None:
            return {
                "success": False,
                "message": "No response from server - connection error or timeout"
            }
        
        # Try to parse JSON response
        try:
            result = response.json()
        except ValueError:
            # Response is not JSON - might be HTML error page or plain text
            return {
                "success": False,
                "message": f"Server error: {response.status_code} - {response.text[:200]}"
            }
        
        # Handle error status codes (400, 500, etc.)
        if response.status_code >= 400:
            # FastAPI returns {"detail": "..."} for HTTPException errors
            error_message = result.get("detail", result.get("message", f"Server error: {response.status_code}"))
            return {
                "success": False,
                "message": error_message,
                "detail": error_message
            }
        
        # Success response
        return result
        
    except Exception as e:
        # Catch any unexpected errors
        return {
            "success": False,
            "message": f"Error making request: {str(e)}"
        }