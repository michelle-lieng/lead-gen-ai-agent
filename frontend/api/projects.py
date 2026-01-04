"""
Project management API client
Matches backend/app/api/routes/projects.py
"""

from typing import Optional
from .base import _request

def get_projects():
    """Fetch all projects from the API"""
    response = _request("GET", "/api/projects/")
    return response.json() if response else []

def create_project(project_name: str, description: Optional[str] = None):
    """Create a new project via API"""
    response = _request("POST", "/api/projects/", json_data={
        "project_name": project_name,
        "description": description
    })
    return response.json() if response else None

def get_project(project_id: int):
    """Get specific project by ID"""
    response = _request("GET", f"/api/projects/{project_id}")
    return response.json() if response else None

def update_project(project_id: int, **kwargs):
    """Update project via API"""
    data = {k: v for k, v in kwargs.items() if v is not None}
    response = _request("PUT", f"/api/projects/{project_id}", json_data=data)
    return response.json() if response else None

def delete_project(project_id: int):
    """Delete project via API"""
    response = _request("DELETE", f"/api/projects/{project_id}")
    if response:
        return {"success": True}
    return None

