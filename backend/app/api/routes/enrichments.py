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

def _enrichment_to_dict(enrichment) -> dict:
    """Convert enrichment model to dictionary with defaults"""
    return {
        "id": enrichment.id,
        "project_id": enrichment.project_id,
        "enrichment_name": enrichment.enrichment_name,
        "column_name": enrichment.column_name,
        "enrichment_description": enrichment.enrichment_description or "",
        "goal": enrichment.goal or "",
        "acceptable_evidence": enrichment.acceptable_evidence or "",
        "result_format": enrichment.result_format or "",
        "result_true_if": enrichment.result_true_if or "",
        "result_false_if": enrichment.result_false_if or "",
        "result_number_value": enrichment.result_number_value or "",
        "result_text_value": enrichment.result_text_value or "",
        "date_added": enrichment.date_added.isoformat() if enrichment.date_added else "",
        "last_updated": enrichment.last_updated.isoformat() if enrichment.last_updated else ""
    }

@router.post("/projects/{project_id}/enrichments/", response_model=dict)
async def create_enrichment(project_id: int, request: EnrichmentCreate):
    """
    Create a new enrichment configuration for a project.
    
    Args:
        project_id: ID of the project
        request: Enrichment creation request with enrichment_name and optional description
    """
    try:
        # Verify project exists
        project = project_service.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)
        
        enrichment = enrichment_service.create_enrichment(
            project_id=project_id,
            enrichment_name=request.enrichment_name,
            column_name=request.column_name,
            enrichment_description=request.enrichment_description
        )
        return {"success": True, "enrichment": _enrichment_to_dict(enrichment)}
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (DuplicateEnrichmentNameError, DuplicateColumnNameError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception(f"❌ Unexpected error creating enrichment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/projects/{project_id}/enrichments/", response_model=List[dict])
async def get_enrichments(project_id: int):
    """
    Get all enrichment configurations for a project.
    """
    try:
        # Verify project exists
        project = project_service.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)
        
        enrichments = enrichment_service.get_enrichments(project_id)
        return [_enrichment_to_dict(e) for e in enrichments]
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception(f"❌ Unexpected error getting enrichments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/enrichments/{enrichment_id}", response_model=dict)
async def get_enrichment(enrichment_id: int):
    """
    Get a specific enrichment configuration by ID.
    """
    try:
        enrichment = enrichment_service.get_enrichment(enrichment_id)
        return _enrichment_to_dict(enrichment)
    except EnrichmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception(f"❌ Unexpected error getting enrichment {enrichment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/enrichments/{enrichment_id}", response_model=dict)
async def update_enrichment(enrichment_id: int, request: EnrichmentUpdate):
    """
    Update an enrichment - all fields are optional, only provided fields will be updated.
    """
    try:
        kwargs = {}
        if request.enrichment_name is not None:
            kwargs["enrichment_name"] = request.enrichment_name
        if request.column_name is not None:
            kwargs["column_name"] = request.column_name
        if request.enrichment_description is not None:
            kwargs["enrichment_description"] = request.enrichment_description
        if request.goal is not None:
            kwargs["goal"] = request.goal
        if request.acceptable_evidence is not None:
            kwargs["acceptable_evidence"] = request.acceptable_evidence
        if request.result_format is not None:
            kwargs["result_format"] = request.result_format
        if request.result_true_if is not None:
            kwargs["result_true_if"] = request.result_true_if
        if request.result_false_if is not None:
            kwargs["result_false_if"] = request.result_false_if
        if request.result_number_value is not None:
            kwargs["result_number_value"] = request.result_number_value
        if request.result_text_value is not None:
            kwargs["result_text_value"] = request.result_text_value
        
        enrichment = enrichment_service.update_enrichment(enrichment_id, **kwargs)
        return {"success": True, "enrichment": _enrichment_to_dict(enrichment)}
    except (DuplicateEnrichmentNameError, DuplicateColumnNameError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EnrichmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception(f"❌ Unexpected error updating enrichment {enrichment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/enrichments/{enrichment_id}")
async def delete_enrichment(enrichment_id: int):
    """
    Delete an enrichment configuration.
    """
    try:
        enrichment_service.delete_enrichment(enrichment_id)
        return {"success": True}
    except EnrichmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception(f"❌ Unexpected error deleting enrichment {enrichment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/projects/{project_id}/enrichments/{enrichment_id}/enrich-leads", response_model=dict)
async def enrich_leads(project_id: int, enrichment_id: int, request: EnrichLeadsRequest):
    """
    Run enrichment on a list of leads using the enrichment configuration.
    
    Args:
        project_id: ID of the project
        enrichment_id: ID of the enrichment configuration to use
        request: Request containing enrichment_id, enrichment_name, result_format, and leads_data
    """
    try:
        # Verify project exists
        project = project_service.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)
        
        # Verify enrichment exists and matches
        enrichment = enrichment_service.get_enrichment(enrichment_id)
        if not enrichment:
            raise EnrichmentNotFoundError(enrichment_id)
        
        # Validate column_name matches
        if enrichment.column_name != request.column_name:
            raise HTTPException(
                status_code=400, 
                detail=f"Column name mismatch. Expected '{enrichment.column_name}', got '{request.column_name}'"
            )
        
        # Validate result_format matches
        if enrichment.result_format != request.result_format:
            raise HTTPException(
                status_code=400,
                detail=f"Result format mismatch. Expected '{enrichment.result_format}', got '{request.result_format}'"
            )
        
        # Validate all required fields are set
        missing_fields = []
        
        if not enrichment.column_name:
            missing_fields.append("Column name")
        if not enrichment.goal:
            missing_fields.append("Goal")
        if not enrichment.acceptable_evidence:
            missing_fields.append("Agent Reasoning")
        if not enrichment.result_format:
            missing_fields.append("Result Format")
        
        # Validate format-specific required fields
        if enrichment.result_format == "True/False":
            if not enrichment.result_true_if:
                missing_fields.append("True if")
            if not enrichment.result_false_if:
                missing_fields.append("False if")
        elif enrichment.result_format == "Number":
            if not enrichment.result_number_value:
                missing_fields.append("Define the Value")
        elif enrichment.result_format == "Text":
            if not enrichment.result_text_value:
                missing_fields.append("What do you want returned")
        
        if missing_fields:
            error_msg = f"The following fields are required before running enrichment: {', '.join(missing_fields)}"
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # Map result_format to output_type for enrich_company
        output_type_map = {
            "True/False": "bool",
            "Text": "str",
            "Number": "int"
        }
        output_type = output_type_map.get(request.result_format)
        if not output_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid result_format: {request.result_format}. Must be one of: True/False, Text, Number"
            )
        
        # Prepare enrichment parameters
        prompt_goal = enrichment.goal
        prompt_reasoning = enrichment.acceptable_evidence
        
        # Prepare type-specific prompts
        string_prompt = enrichment.result_text_value or ""
        is_true_prompt = enrichment.result_true_if or ""
        is_false_prompt = enrichment.result_false_if or ""
        int_prompt = enrichment.result_number_value or ""
        
        # Process each lead
        enriched_leads = []
        for lead_row in request.leads_data:
            company_name = lead_row.get("lead", "")
            if not company_name:
                # Skip leads without a "lead" field
                continue
            
            try:
                # Run enrichment for this company (use column_name for the output model)
                result = await enrichment_execution_service.enrich_company(
                    company_name=company_name,
                    enrichment_name=request.column_name,  # Use column_name for the output model
                    prompt_goal=prompt_goal,
                    prompt_reasoning=prompt_reasoning,
                    output_type=output_type,
                    string_prompt=string_prompt,
                    is_false_prompt=is_false_prompt,
                    is_true_prompt=is_true_prompt,
                    int_prompt=int_prompt,
                    return_metadata=False
                )
                
                # Create enriched lead row
                enriched_lead = lead_row.copy()
                
                # Extract the enrichment value, reasoning, and evidence from result
                # Result has keys like: column_name, column_name_reasoning, column_name_evidence
                enrichment_value = result.get(request.column_name)
                enrichment_reasoning = result.get(f"{request.column_name}_reasoning", "")
                enrichment_evidence = result.get(f"{request.column_name}_evidence", "")
                
                enriched_lead[request.column_name] = enrichment_value
                enriched_lead[f"{request.column_name}_reasoning"] = enrichment_reasoning
                enriched_lead[f"{request.column_name}_evidence"] = enrichment_evidence
                
                enriched_leads.append(enriched_lead)
                
            except Exception as e:
                logger.error(f"❌ Error enriching lead '{company_name}': {e}")
                # Continue with other leads even if one fails
                # Add the lead with None values for enrichment fields
                enriched_lead = lead_row.copy()
                enriched_lead[request.column_name] = None
                enriched_lead[f"{request.column_name}_reasoning"] = ""
                enriched_lead[f"{request.column_name}_evidence"] = ""
                enriched_leads.append(enriched_lead)
        
        # Get columns list
        columns = list(enriched_leads[0].keys()) if enriched_leads else ["lead"]
        # Ensure enrichment columns are in the list (they should already be there, but just in case)
        if request.column_name not in columns:
            columns.append(request.column_name)
        if f"{request.column_name}_reasoning" not in columns:
            columns.append(f"{request.column_name}_reasoning")
        if f"{request.column_name}_evidence" not in columns:
            columns.append(f"{request.column_name}_evidence")
        
        # Automatically save enrichment results to merged_results table
        save_result = merged_results_service.save_ai_enrichment_results(
            project_id=project_id,
            column_name=request.column_name,
            enriched_leads=enriched_leads
        )
        logger.info(f"✅ Automatically saved enrichment results to merged_results: {save_result.get('message', '')}")
        return {
            "success": True,
            "message": f"Enrichment '{enrichment.enrichment_name}' (column: {request.column_name}) processed successfully on {len(enriched_leads)} lead(s) for project {project_id}",
            "leads_processed": len(enriched_leads),
            "enrichment_id": enrichment_id,
            "project_id": project_id,
            "enriched_leads": enriched_leads,
            "columns": columns
        }
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EnrichmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"❌ Unexpected error enriching leads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/projects/{project_id}/enrichments/{enrichment_id}/test-enrich-leads", response_model=dict)
async def test_enrich_leads(project_id: int, enrichment_id: int, request: EnrichLeadsRequest):
    """
    Run test enrichment on a list of leads using the enrichment configuration.
    
    Args:
        project_id: ID of the project
        enrichment_id: ID of the enrichment configuration to use
        request: Request containing enrichment_id, enrichment_name, result_format, and leads_data
    """
    try:
        # Verify project exists
        project = project_service.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(project_id)
        
        # Verify enrichment exists and matches
        enrichment = enrichment_service.get_enrichment(enrichment_id)
        if not enrichment:
            raise EnrichmentNotFoundError(enrichment_id)
        
        # Validate column_name matches
        if enrichment.column_name != request.column_name:
            raise HTTPException(
                status_code=400, 
                detail=f"Column name mismatch. Expected '{enrichment.column_name}', got '{request.column_name}'"
            )
        
        # Validate result_format matches
        if enrichment.result_format != request.result_format:
            raise HTTPException(
                status_code=400,
                detail=f"Result format mismatch. Expected '{enrichment.result_format}', got '{request.result_format}'"
            )
        
        # Validate all required fields are set
        missing_fields = []
        
        if not enrichment.column_name:
            missing_fields.append("Column name")
        if not enrichment.goal:
            missing_fields.append("Goal")
        if not enrichment.acceptable_evidence:
            missing_fields.append("Agent Reasoning")
        if not enrichment.result_format:
            missing_fields.append("Result Format")
        
        # Validate format-specific required fields
        if enrichment.result_format == "True/False":
            if not enrichment.result_true_if:
                missing_fields.append("True if")
            if not enrichment.result_false_if:
                missing_fields.append("False if")
        elif enrichment.result_format == "Number":
            if not enrichment.result_number_value:
                missing_fields.append("Define the Value")
        elif enrichment.result_format == "Text":
            if not enrichment.result_text_value:
                missing_fields.append("What do you want returned")
        
        if missing_fields:
            error_msg = f"The following fields are required before running enrichment: {', '.join(missing_fields)}"
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # Map result_format to output_type for enrich_company
        output_type_map = {
            "True/False": "bool",
            "Text": "str",
            "Number": "int"
        }
        output_type = output_type_map.get(request.result_format)
        if not output_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid result_format: {request.result_format}. Must be one of: True/False, Text, Number"
            )
        
        # Prepare enrichment parameters
        prompt_goal = enrichment.goal
        prompt_reasoning = enrichment.acceptable_evidence
        
        # Prepare type-specific prompts
        string_prompt = enrichment.result_text_value or ""
        is_true_prompt = enrichment.result_true_if or ""
        is_false_prompt = enrichment.result_false_if or ""
        int_prompt = enrichment.result_number_value or ""
        
        # Process each lead
        enriched_leads = []
        for lead_row in request.leads_data:
            company_name = lead_row.get("lead", "")
            if not company_name:
                # Skip leads without a "lead" field
                continue
            
            try:
                # Run enrichment for this company (use column_name for the output model)
                result = await enrichment_execution_service.enrich_company(
                    company_name=company_name,
                    enrichment_name=request.column_name,  # Use column_name for the output model
                    prompt_goal=prompt_goal,
                    prompt_reasoning=prompt_reasoning,
                    output_type=output_type,
                    string_prompt=string_prompt,
                    is_false_prompt=is_false_prompt,
                    is_true_prompt=is_true_prompt,
                    int_prompt=int_prompt,
                    return_metadata=False
                )
                
                # Create enriched lead row
                enriched_lead = lead_row.copy()
                
                # Extract the enrichment value, reasoning, and evidence from result
                # Result has keys like: column_name, column_name_reasoning, column_name_evidence
                enrichment_value = result.get(request.column_name)
                enrichment_reasoning = result.get(f"{request.column_name}_reasoning", "")
                enrichment_evidence = result.get(f"{request.column_name}_evidence", "")
                
                enriched_lead[request.column_name] = enrichment_value
                enriched_lead[f"{request.column_name}_reasoning"] = enrichment_reasoning
                enriched_lead[f"{request.column_name}_evidence"] = enrichment_evidence
                
                enriched_leads.append(enriched_lead)
                
            except Exception as e:
                logger.error(f"❌ Error enriching lead '{company_name}': {e}")
                # Continue with other leads even if one fails
                # Add the lead with None values for enrichment fields
                enriched_lead = lead_row.copy()
                enriched_lead[request.column_name] = None
                enriched_lead[f"{request.column_name}_reasoning"] = ""
                enriched_lead[f"{request.column_name}_evidence"] = ""
                enriched_leads.append(enriched_lead)
        
        # Get columns list
        columns = list(enriched_leads[0].keys()) if enriched_leads else ["lead"]
        # Ensure enrichment columns are in the list (they should already be there, but just in case)
        if request.column_name not in columns:
            columns.append(request.column_name)
        if f"{request.column_name}_reasoning" not in columns:
            columns.append(f"{request.column_name}_reasoning")
        if f"{request.column_name}_evidence" not in columns:
            columns.append(f"{request.column_name}_evidence")
        
        # Automatically save enrichment results to merged_results table
        return {
            "success": True,
            "message": f"Enrichment '{enrichment.enrichment_name}' (column: {request.column_name}) processed successfully on {len(enriched_leads)} lead(s) for project {project_id}",
            "leads_processed": len(enriched_leads),
            "enrichment_id": enrichment_id,
            "project_id": project_id,
            "enriched_leads": enriched_leads,
            "columns": columns
        }
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EnrichmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseFailureError as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"❌ Unexpected error enriching leads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")