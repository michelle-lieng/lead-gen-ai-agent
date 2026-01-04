"""
Enrichment API client
Matches backend/app/api/routes/enrichments.py
"""

from typing import Optional
from .base import _request


def create_enrichment(project_id: int, enrichment_name: str, enrichment_description: Optional[str] = None):
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


def update_enrichment(enrichment_id: int, **kwargs):
    """Update an enrichment via API - all fields are optional"""
    data = {k: v for k, v in kwargs.items() if v is not None}
    
    response = _request("PUT", f"/api/enrichments/{enrichment_id}", json_data=data)
    return response.json() if response else None


def delete_enrichment(enrichment_id: int):
    """Delete an enrichment via API"""
    response = _request("DELETE", f"/api/enrichments/{enrichment_id}")
    if response:
        return {"success": True}
    return None


def enrich_leads(project_id: int, enrichment_id: int, leads_data: list):
    """Run enrichment on leads and add enrichment column via API
    
    Args:
        project_id: Project ID
        enrichment_id: Enrichment ID
        leads_data: List of lead dictionaries e.g. [{"lead": "Acme Corp", "serp_count": 5, "bcorp_certified": True}, {...},...]
    """
    response = _request("POST", f"/api/projects/{project_id}/enrichments/{enrichment_id}/enrich-leads", json_data={
        "leads_data": leads_data
    })
    return response.json() if response else None


def test_enrich_leads(project_id: int, enrichment_id: int, leads_data: list):
    """Run test enrichment on leads and add enrichment column via API"""    
    response = _request("POST", f"/api/projects/{project_id}/enrichments/{enrichment_id}/test-enrich-leads", json_data={
        "leads_data": leads_data
    })
    return response.json() if response else None

