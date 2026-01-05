"""
Enrichment endpoints
"""

import logging
from fastapi import APIRouter
from typing import List

from ...services.enrichment_execution_service import enrichment_execution_service
from ...services.enrichment_service import enrichment_service
from ...services.merged_results_service import merged_results_service
from ...services.job_service import job_service
from ...models.schemas import (
    EnrichmentCreate,
    EnrichmentUpdate,
    EnrichmentResponse,
    EnrichLeadsRequest,
    JobResponse,
)
from ...exceptions import EnrichmentNotFoundError, ProjectNotFoundError
from ...services.project_service import project_service
from ...models.schemas import (
    EnrichmentCreate,
    EnrichmentUpdate,
    EnrichmentResponse,
    EnrichLeadsRequest,
)
from ...exceptions import (
    EnrichmentNotFoundError,
    ProjectNotFoundError,
    NoLeadsToEnrichError,
)

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
        enrichment_description=request.enrichment_description,
    )


@router.get(
    "/projects/{project_id}/enrichments/", response_model=List[EnrichmentResponse]
)
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


@router.post(
    "/projects/{project_id}/enrichments/{enrichment_id}/enrich-leads",
    response_model=dict,
)
async def enrich_leads(
    project_id: int, enrichment_id: int, request: EnrichLeadsRequest
):
    """
    Run enrichment on a list of leads using the enrichment configuration.

    Args:
        project_id: ID of the project
        enrichment_id: ID of the enrichment configuration to use
        request: Request containing leads_data
    """
    # Verify project exists
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # Verify enrichment exists
    enrichment = enrichment_service.get_enrichment(enrichment_id)
    if not enrichment:
        raise EnrichmentNotFoundError(enrichment_id)

    # Validate that leads_data is not empty
    if not request.leads_data or len(request.leads_data) == 0:
        raise NoLeadsToEnrichError()

    # Check if there is a running job
    job_service.check_running_job(project_id, "enrich_leads", enrichment_id)

    # Create job
    job = job_service.create_job(project_id, "enrich_leads", enrichment_id)

    # Process leads enrichment using enrichment's configured values
    enriched_leads, columns = await enrichment_execution_service.enrich_leads(
        enrichment=enrichment, leads_data=request.leads_data
    )

    # Automatically save enrichment results to merged_results table
    merged_results_service.save_ai_enrichment_results(
        project_id=project_id,
        column_name=enrichment.column_name,
        enriched_leads=enriched_leads,
    )

    job_service.mark_job_as_completed(job.id)

    return {
        "success": True,
        "message": f"Enrichment '{enrichment.enrichment_name}' completed on {len(enriched_leads)} lead(s). Results saved to merged leads.",
        "leads_processed": len(enriched_leads),
        "enrichment_id": enrichment_id,
        "project_id": project_id,
        "enriched_leads": enriched_leads,
        "columns": columns,
    }


@router.post(
    "/projects/{project_id}/enrichments/{enrichment_id}/test-enrich-leads",
    response_model=dict,
)
async def test_enrich_leads(
    project_id: int, enrichment_id: int, request: EnrichLeadsRequest
):
    """
    Run test enrichment on a list of leads using the enrichment configuration.
    Does not save results to merged_results table.

    Args:
        project_id: ID of the project
        enrichment_id: ID of the enrichment configuration to use
        request: Request containing leads_data
    """
    # Verify project exists
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # Verify enrichment exists
    enrichment = enrichment_service.get_enrichment(enrichment_id)
    if not enrichment:
        raise EnrichmentNotFoundError(enrichment_id)

    # Validate that leads_data is not empty
    if not request.leads_data or len(request.leads_data) == 0:
        raise NoLeadsToEnrichError()

    # Check if there is a running job
    job_service.check_running_job(project_id, "enrich_leads", enrichment_id)

    # Create job
    job = job_service.create_job(project_id, "enrich_leads", enrichment_id)

    # Process leads enrichment using enrichment's configured values
    enriched_leads, columns = await enrichment_execution_service.enrich_leads(
        enrichment=enrichment, leads_data=request.leads_data
    )

    job_service.mark_job_as_completed(job.id)

    # Return results without saving (test mode)
    return {
        "success": True,
        "message": f"Test enrichment '{enrichment.enrichment_name}' completed on {len(enriched_leads)} lead(s)",
        "leads_processed": len(enriched_leads),
        "enrichment_id": enrichment_id,
        "project_id": project_id,
        "enriched_leads": enriched_leads,
        "columns": columns,
    }
