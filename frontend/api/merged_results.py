"""
Merged results API client
Matches backend/app/api/routes/merged_results.py
"""

from .base import _request


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

