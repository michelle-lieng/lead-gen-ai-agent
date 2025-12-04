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
BASE_URL = "http://localhost:8000"
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
        
        if response.status_code >= 200 and response.status_code < 300:
            return response
        return None
    except Exception:
        return None

# Project endpoints
def get_projects():
    """Fetch all projects from the API"""
    response = _request("GET", "/api/projects/")
    return response.json() if response else []

def create_project(project_name: str, description: Optional[str]=None, query_search_target: Optional[str]=None):
    """Create a new project via API"""
    response = _request("POST", "/api/projects/", json_data={"project_name": project_name, "description": description, "query_search_target": query_search_target})
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
def upload_dataset(project_id: int, dataset_name: str, lead_column: str, enrichment_column_list: list[str], enrichment_column_exists: bool, csv_file):
    """Upload a CSV dataset for a project via API"""
    csv_file.seek(0)
    file_content = csv_file.read()
    csv_file.seek(0)
    
    files = {'csv_file': (csv_file.name, file_content, 'text/csv')}
    form_data = {
        'dataset_name': dataset_name,
        'lead_column': lead_column,
        'enrichment_column_list': json.dumps(enrichment_column_list) if enrichment_column_list else None,
        'enrichment_column_exists': 'true' if enrichment_column_exists else 'false'
    }
    
    response = _request("POST", f"/api/projects/{project_id}/datasets", files=files, form_data=form_data)
    return response.json() if response else None


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

# Test lead extraction prompts endpoints
def generate_test_urls(project_id: int, query: str):
    """Generate test URLs from a search query and save them to test_serp_urls table"""
    response = _request("POST", f"/api/projects/{project_id}/test/urls", json_data={"query": query})
    return response.json() if response else None

def get_test_urls(project_id: int):
    """Get all test URLs for a project"""
    response = _request("GET", f"/api/projects/{project_id}/test/urls")
    return response.json() if response else []

def create_test_url(project_id: int, link: str, title: str = None, snippet: str = None):
    """Create a new test URL"""
    data = {
        "link": link
    }
    if title is not None:
        data["title"] = title
    if snippet is not None:
        data["snippet"] = snippet
    
    response = _request("POST", f"/api/projects/{project_id}/test/urls/create", json_data=data)
    return response.json() if response else None

def update_test_url(project_id: int, url_id: int, title: str = None, snippet: str = None, link: str = None):
    """Update a test URL"""
    data = {}
    if title is not None:
        data["title"] = title
    if snippet is not None:
        data["snippet"] = snippet
    if link is not None:
        data["link"] = link
    
    response = _request("PUT", f"/api/projects/{project_id}/test/urls/{url_id}", json_data=data)
    return response.json() if response else None

def delete_test_url(project_id: int, url_id: int):
    """Delete a test URL"""
    response = _request("DELETE", f"/api/projects/{project_id}/test/urls/{url_id}")
    return response.json() if response else None

def extract_test_leads(project_id: int):
    """Extract leads from test URLs and return them (without saving to database)"""
    response = _request("POST", f"/api/projects/{project_id}/test/leads")
    return response.json() if response else None