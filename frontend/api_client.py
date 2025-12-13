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

def create_url(project_id: int, link: str, title: str = None, snippet: str = None):
    """Create a new production URL (query is automatically set to 'Manual Entry' in the backend)"""
    data = {
        "link": link
    }
    if title is not None:
        data["title"] = title
    if snippet is not None:
        data["snippet"] = snippet
    # Note: query is automatically set to "Manual Entry" in the backend
    
    response = _request("POST", f"/api/projects/{project_id}/urls/create", json_data=data)
    return response.json() if response else None

def update_url(project_id: int, url_id: int, title: str = None, snippet: str = None, link: str = None):
    """Update a production URL"""
    data = {}
    if title is not None:
        data["title"] = title
    if snippet is not None:
        data["snippet"] = snippet
    if link is not None:
        data["link"] = link
    
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

# Mock enrichment storage (in-memory, will reset on server restart)
def _ensure_enrichment_defaults(enrichment: dict) -> dict:
    """Ensure optional result fields exist."""
    enrichment.setdefault("result_true_if", "")
    enrichment.setdefault("result_false_if", "")
    enrichment.setdefault("result_number_value", "")
    enrichment.setdefault("result_text_value", "")
    return enrichment

_mock_enrichments = [
    {
        "id": 1,
        "enrichment_name": "company_size",
        "enrichment_description": "Number of employees in the company",
        "goal": "Extract the number of employees or company size information from lead data",
        "acceptable_evidence": "Company website, LinkedIn profile, job postings, news articles mentioning employee count",
        "result_format": "Number",
        "result_true_if": "",
        "result_false_if": "",
        "result_number_value": "Number of employees (approximate)",
        "result_text_value": "",
        "date_added": "2025-01-15T10:30:00",
        "last_updated": "2025-01-15T10:30:00"
    },
    {
        "id": 2,
        "enrichment_name": "industry_sector",
        "enrichment_description": "Primary industry or business sector",
        "goal": "Identify the primary industry or business sector that the company operates in",
        "acceptable_evidence": "Company website, About page, product descriptions, industry classifications",
        "result_format": "Text",
        "result_true_if": "",
        "result_false_if": "",
        "result_number_value": "",
        "result_text_value": "Industry sector name",
        "date_added": "2025-01-15T11:00:00",
        "last_updated": "2025-01-15T11:00:00"
    },
    {
        "id": 3,
        "enrichment_name": "revenue_range",
        "enrichment_description": "Annual revenue bracket",
        "goal": "Determine the annual revenue range or bracket for the company",
        "acceptable_evidence": "Financial reports, company filings, news articles, industry databases",
        "result_format": "Text",
        "result_true_if": "",
        "result_false_if": "",
        "result_number_value": "",
        "result_text_value": "Revenue range (e.g., $10M-$50M)",
        "date_added": "2025-01-15T11:15:00",
        "last_updated": "2025-01-15T11:15:00"
    }
]
_mock_enrichment_counter = 4  # Next ID to use

def create_enrichment(enrichment_name: str, enrichment_description: Optional[str]=None):
    """Create a new enrichment via API (MOCK - in-memory storage)"""
    global _mock_enrichments, _mock_enrichment_counter
    
    # Check if name already exists
    if any(e['enrichment_name'] == enrichment_name for e in _mock_enrichments):
        raise Exception(f"Enrichment name '{enrichment_name}' already exists")
    
    from datetime import datetime
    now = datetime.now().isoformat()
    
    new_enrichment = _ensure_enrichment_defaults({
        "id": _mock_enrichment_counter,
        "enrichment_name": enrichment_name,
        "enrichment_description": enrichment_description or "",
        "goal": "",
        "acceptable_evidence": "",
        "result_format": "",
        "result_true_if": "",
        "result_false_if": "",
        "result_number_value": "",
        "result_text_value": "",
        "date_added": now,
        "last_updated": now
    })
    
    _mock_enrichments.append(new_enrichment)
    _mock_enrichment_counter += 1
    
    return {"success": True, "enrichment": new_enrichment}

def get_enrichments():
    """Get all enrichments from the API (MOCK - returns in-memory data)"""
    return [_ensure_enrichment_defaults(e.copy()) for e in _mock_enrichments]

def get_enrichment(enrichment_id: int):
    """Get a specific enrichment by ID from the API (MOCK - returns in-memory data)"""
    for enrichment in _mock_enrichments:
        if enrichment['id'] == enrichment_id:
            return _ensure_enrichment_defaults(enrichment.copy())
    return None

def update_enrichment(enrichment_id: int, enrichment_description: Optional[str]=None):
    """Update an enrichment via API (MOCK - in-memory storage)"""
    global _mock_enrichments
    
    from datetime import datetime
    
    for enrichment in _mock_enrichments:
        if enrichment['id'] == enrichment_id:
            if enrichment_description is not None:
                enrichment['enrichment_description'] = enrichment_description
            enrichment['last_updated'] = datetime.now().isoformat()
            return {"success": True, "enrichment": enrichment}
    
    return None

def update_enrichment_fields(
    enrichment_id: int,
    goal: Optional[str]=None,
    acceptable_evidence: Optional[str]=None,
    result_format: Optional[str]=None,
    result_true_if: Optional[str]=None,
    result_false_if: Optional[str]=None,
    result_number_value: Optional[str]=None,
    result_text_value: Optional[str]=None
):
    """Update enrichment configuration fields (MOCK - in-memory storage)"""
    global _mock_enrichments
    
    from datetime import datetime
    
    for enrichment in _mock_enrichments:
        if enrichment['id'] == enrichment_id:
            enrichment = _ensure_enrichment_defaults(enrichment)
            if goal is not None:
                enrichment['goal'] = goal
            if acceptable_evidence is not None:
                enrichment['acceptable_evidence'] = acceptable_evidence
            if result_format is not None:
                enrichment['result_format'] = result_format
            if result_true_if is not None:
                enrichment['result_true_if'] = result_true_if
            if result_false_if is not None:
                enrichment['result_false_if'] = result_false_if
            if result_number_value is not None:
                enrichment['result_number_value'] = result_number_value
            if result_text_value is not None:
                enrichment['result_text_value'] = result_text_value
            enrichment['last_updated'] = datetime.now().isoformat()
            return {"success": True, "enrichment": enrichment}
    
    return None

def delete_enrichment(enrichment_id: int):
    """Delete an enrichment via API (MOCK - in-memory storage)"""
    global _mock_enrichments
    
    for i, enrichment in enumerate(_mock_enrichments):
        if enrichment['id'] == enrichment_id:
            _mock_enrichments.pop(i)
            return True
    
    return False

def enrich_leads(project_id: int, enrichment_id: int, leads_data: list, enrichment_name: str, result_format: str):
    """Run enrichment on leads and add enrichment column (MOCK - simulates API call)"""
    import time
    import random
    
    if not enrichment_name:
        return {
            "success": False,
            "message": "Enrichment name is required to add enrichment column.",
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
    
    # Simulate processing time
    time.sleep(1)
    
    # Add enrichment column to each lead
    updated_leads = []
    
    for lead_row in leads_data:
        # Create a copy of the lead row
        updated_lead = lead_row.copy()
        
        # Generate mock value based on result_format
        if result_format == "True/False":
            # Mock: randomly assign True/False
            updated_lead[enrichment_name] = random.choice([True, False])
        elif result_format == "Text":
            # Mock: generate sample text
            updated_lead[enrichment_name] = f"Sample text for {lead_row.get('lead', 'lead')}"
        elif result_format == "Number":
            # Mock: generate random number
            updated_lead[enrichment_name] = random.randint(1, 100)
        else:
            # Default: empty string
            updated_lead[enrichment_name] = ""
        
        updated_leads.append(updated_lead)
    
    # Update columns list if needed
    columns = list(updated_leads[0].keys()) if updated_leads else []
    if enrichment_name not in columns:
        columns.append(enrichment_name)
    
    return {
        "success": True,
        "message": f"Enrichment '{enrichment_name}' processed successfully on {len(updated_leads)} lead(s) for project {project_id}",
        "leads_processed": len(updated_leads),
        "enrichment_id": enrichment_id,
        "project_id": project_id,
        "enriched_leads": updated_leads,
        "columns": columns
    }