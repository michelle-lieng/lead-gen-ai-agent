"""
Enrichment endpoints
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import List

from ...services.enrichment_execution_service import enrichment_execution_service
from ...services.enrichment_service import enrichment_service
from ...services.merged_results_service import merged_results_service
from ...models.schemas import (
    EnrichmentCreate, 
    EnrichmentUpdate, 
    EnrichmentResponse,
    EnrichLeadsRequest
)
from ...exceptions import (
    DuplicateEnrichmentNameError,
    DuplicateColumnNameError,
    EnrichmentNotFoundError, 
    DatabaseFailureError,
    ProjectNotFoundError
)
from ...services.project_service import project_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/projects/{project_id}/enrichments/", response_model=EnrichmentResponse)
async def create_enrichment(project_id: int, request: EnrichmentCreate):
    """
    Create a new enrichment configuration for a project.
    
    Args:
        project_id: ID of the project
        request: Enrichment creation request with enrichment_name and optional description
    """
    # Verify project exists
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    
    return enrichment_service.create_enrichment(
        project_id=project_id,
        enrichment_name=request.enrichment_name,
        column_name=request.column_name,
        enrichment_description=request.enrichment_description
    )

@router.get("/projects/{project_id}/enrichments/", response_model=List[EnrichmentResponse])
async def get_enrichments(project_id: int):
    """
    Get all enrichment configurations for a project.
    """
    # Verify project exists
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    
    return enrichment_service.get_enrichments(project_id)

@router.get("/enrichments/{enrichment_id}", response_model=EnrichmentResponse)
async def get_enrichment(enrichment_id: int):
    """
    Get a specific enrichment configuration by ID.
    """
    return enrichment_service.get_enrichment(enrichment_id)

@router.put("/enrichments/{enrichment_id}", response_model=EnrichmentResponse)
async def update_enrichment(enrichment_id: int, request: EnrichmentUpdate):
    """
    Update an enrichment - all fields are optional, only provided fields will be updated.
    """
    update_data = request.dict(exclude_unset=True)
    return enrichment_service.update_enrichment(enrichment_id, **update_data)

@router.delete("/enrichments/{enrichment_id}", status_code=204)
async def delete_enrichment(enrichment_id: int):
    """
    Delete an enrichment configuration.
    """
    enrichment_service.delete_enrichment(enrichment_id)
    return

@router.post("/projects/{project_id}/enrichments/{enrichment_id}/enrich-leads", response_model=dict)
async def enrich_leads(project_id: int, enrichment_id: int, request: EnrichLeadsRequest):
    """
    Run enrichment on a list of leads using the enrichment configuration.
    
    Args:
        project_id: ID of the project
        enrichment_id: ID of the enrichment configuration to use
        request: Request containing enrichment_id, enrichment_name, result_format, and leads_data
    """
    # Verify project exists
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    
    # Verify enrichment exists
    enrichment = enrichment_service.get_enrichment(enrichment_id)
    if not enrichment:
        raise EnrichmentNotFoundError(enrichment_id)
    
    # Validate enrichment configuration
    is_valid, error_msg, missing_fields = enrichment_service.validate_enrichment_config(
        enrichment,
        request.column_name,
        request.result_format
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Process leads enrichment
    enriched_leads, columns = await enrichment_service.process_leads_enrichment(
        enrichment=enrichment,
        leads_data=request.leads_data,
        column_name=request.column_name,
        enrichment_execution_service=enrichment_execution_service
    )
    
    # Calculate success/failure statistics
    successful = sum(1 for lead in enriched_leads if lead.get(request.column_name) is not None)
    failed = len(enriched_leads) - successful
    
    # Automatically save enrichment results to merged_results table
    save_result = merged_results_service.save_ai_enrichment_results(
        project_id=project_id,
        column_name=request.column_name,
        enriched_leads=enriched_leads
    )
    logger.info(f"✅ Automatically saved enrichment results to merged_results: {save_result.get('message', '')}")
    
    return {
        "success": True,
        "message": f"Enrichment '{enrichment.enrichment_name}' (column: {request.column_name}) completed: {successful} successful, {failed} failed",
        "leads_processed": len(enriched_leads),
        "successful": successful,
        "failed": failed,
        "enrichment_id": enrichment_id,
        "project_id": project_id,
        "enriched_leads": enriched_leads,
        "columns": columns
    }

@router.post("/projects/{project_id}/enrichments/{enrichment_id}/test-enrich-leads", response_model=dict)
async def test_enrich_leads(project_id: int, enrichment_id: int, request: EnrichLeadsRequest):
    """
    Run test enrichment on a list of leads using the enrichment configuration.
    Does not save results to merged_results table.
    
    Args:
        project_id: ID of the project
        enrichment_id: ID of the enrichment configuration to use
        request: Request containing enrichment_id, enrichment_name, result_format, and leads_data
    """
    # Verify project exists
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    
    # Verify enrichment exists
    enrichment = enrichment_service.get_enrichment(enrichment_id)
    if not enrichment:
        raise EnrichmentNotFoundError(enrichment_id)
    
    # Validate enrichment configuration
    is_valid, error_msg, missing_fields = enrichment_service.validate_enrichment_config(
        enrichment,
        request.column_name,
        request.result_format
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Process leads enrichment
    enriched_leads, columns = await enrichment_service.process_leads_enrichment(
        enrichment=enrichment,
        leads_data=request.leads_data,
        column_name=request.column_name,
        enrichment_execution_service=enrichment_execution_service
    )
    
    # Calculate success/failure statistics
    successful = sum(1 for lead in enriched_leads if lead.get(request.column_name) is not None)
    failed = len(enriched_leads) - successful
    
    # Return results without saving (test mode)
    return {
        "success": True,
        "message": f"Test enrichment '{enrichment.enrichment_name}' (column: {request.column_name}) completed: {successful} successful, {failed} failed",
        "leads_processed": len(enriched_leads),
        "successful": successful,
        "failed": failed,
        "enrichment_id": enrichment_id,
        "project_id": project_id,
        "enriched_leads": enriched_leads,
        "columns": columns
    }