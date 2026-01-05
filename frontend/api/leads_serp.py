"""
SERP-based lead generation API client
Matches backend/app/api/routes/leads_serp.py
"""

from .base import _request


def generate_queries(project_id: int, num_queries: int = 3):
    """
    Generate search queries for a project via API
    
    Args:
        project_id: ID of the project
        num_queries: Number of queries to generate (1-20, default: 3)
    """
    response = _request("POST", f"/api/projects/{project_id}/queries", json_data={"num_queries": num_queries})
    return response.json()


def get_queries(project_id: int):
    """
    Get all queries for a project from the database via API
    
    Args:
        project_id: ID of the project
    """
    response = _request("GET", f"/api/projects/{project_id}/queries")
    return response.json()


def generate_urls(project_id: int, queries: list[str]):
    """Generate URLs from search queries and save them"""
    response = _request("POST", f"/api/projects/{project_id}/urls", json_data={"queries": queries})
    return response.json()


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
    return response.json()


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
    return response.json()


def delete_url(project_id: int, url_id: int):
    """Delete a production URL (backend returns 204 No Content)"""
    response = _request("DELETE", f"/api/projects/{project_id}/urls/{url_id}")
    return {"success": True}

def generate_leads(project_id: int):
    """Extract leads from URLs and save them"""
    response = _request("POST", f"/api/projects/{project_id}/leads")
    return response.json()


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

