"""
Enrichment endpoints
"""

import logging
from fastapi import APIRouter, Depends

from ..deps import ApiKeys, get_api_keys
from ...services.agent_brief_service import agent_brief_service
from ...services.enrichment_execution_service import enrichment_execution_service
from ...services.column_gaps import unanswered_columns
from ...services.enrichment_service import enrichment_service
from ...services.merged_results_service import merged_results_service
from ...services.job_service import job_service
from ...models.schemas import (
    ContinueColumn,
    EnrichmentCreate,
    EnrichmentUpdate,
    EnrichmentResponse,
    EnrichLeadsRequest,
    EnrichmentDraftRequest,
)
from ...services.project_service import project_service
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


@router.post(
    "/projects/{project_id}/enrichments/draft", response_model=EnrichmentResponse
)
async def draft_enrichment(
    project_id: int,
    request: EnrichmentDraftRequest,
    keys: ApiKeys = Depends(get_api_keys),
):
    """
    Create a fully configured enrichment from one plain-English instruction.

    The caller sends something like "does this clinic have more than one
    doctor?" and gets back an enrichment with its column name, goal, evidence
    standard and result format already filled in, ready to run. The stored
    shape is identical to a hand-configured enrichment.
    """
    project = project_service.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    return agent_brief_service.draft_enrichment(
        project_id,
        request.instruction,
        openai_api_key=keys.require_openai(),
        result_format=request.result_format,
    )


@router.get(
    "/projects/{project_id}/enrichments/", response_model=list[EnrichmentResponse]
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


@router.get(
    "/projects/{project_id}/enrichments/unanswered",
    response_model=list[ContinueColumn],
)
async def get_unanswered_columns(project_id: int):
    """
    Columns that still have leads without an answer, with those leads.

    Called after a search adds rows, so every existing column can be filled
    for the new rows without re-researching the ones already answered.
    """
    project_service.get_project(project_id)  # raises if the project is gone
    rows = merged_results_service.get_merged_results(project_id)["data"]
    return unanswered_columns(rows, enrichment_service.get_enrichments(project_id))


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
    project_id: int,
    enrichment_id: int,
    request: EnrichLeadsRequest,
    keys: ApiKeys = Depends(get_api_keys),
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

    # Require the caller's API keys up front (before creating a job)
    openai_api_key = keys.require_openai()
    jina_api_key = keys.require_jina()

    running_job = job_service.check_running_job(project_id, "enrich_leads", enrichment_id)

    job = job_service.create_job(project_id, "enrichments", enrichment_id)
    # Process leads enrichment using enrichment's configured values
    enriched_leads, columns = await enrichment_execution_service.enrich_leads(
        enrichment=enrichment,
        leads_data=request.leads_data,
        project_id=project_id,
        enrichment_id=enrichment_id,
        job_id=job.id,
        openai_api_key=openai_api_key,
        jina_api_key=jina_api_key,
    )

    # Automatically save enrichment results to merged_results table
    merged_results_service.save_ai_enrichment_results(
        project_id=project_id,
        column_name=enrichment.column_name,
        enriched_leads=enriched_leads,
    )

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
    project_id: int,
    enrichment_id: int,
    request: EnrichLeadsRequest,
    keys: ApiKeys = Depends(get_api_keys),
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

    # Require the caller's API keys up front (before creating a job)
    openai_api_key = keys.require_openai()
    jina_api_key = keys.require_jina()

    # Check if there is a running job
    job_service.check_running_job(project_id, "enrich_leads", enrichment_id)

    # Create job
    job = job_service.create_job(project_id, "test_enrichments", enrichment_id)

    # Process leads enrichment using enrichment's configured values
    enriched_leads, columns = await enrichment_execution_service.enrich_leads(
        enrichment=enrichment,
        leads_data=request.leads_data,
        project_id=project_id,
        enrichment_id=enrichment_id,
        job_id=job.id,
        openai_api_key=openai_api_key,
        jina_api_key=jina_api_key,
    )

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
