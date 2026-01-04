"""
Enrichment service for managing enrichment operations
"""
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_
from typing import List, Optional, Dict, Any, Tuple
import logging
import openai

from ..models.tables import Enrichment
from .database_service import db_service
from ..exceptions import (
    DuplicateEnrichmentNameError, 
    DuplicateColumnNameError, 
    EnrichmentNotFoundError, 
    DatabaseFailureError,
    ExternalScraperError,
    OpenAITokenLimitExceededError,
    ApiKeyNotConfiguredError
)

logger = logging.getLogger(__name__)

class EnrichmentService:
    """Service for enrichment-related database operations"""

    def validate_enrichment_config(
        self,
        enrichment: Enrichment,
        expected_column_name: str,
        expected_result_format: str
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Validate enrichment configuration before execution.
        
        Returns:
            Tuple of (is_valid, error_message, missing_fields)
        """
        # Validate column_name matches
        if enrichment.column_name != expected_column_name:
            return (
                False,
                f"Column name mismatch. Expected '{enrichment.column_name}', got '{expected_column_name}'",
                None
            )
        
        # Validate result_format matches
        if enrichment.result_format != expected_result_format:
            return (
                False,
                f"Result format mismatch. Expected '{enrichment.result_format}', got '{expected_result_format}'",
                None
            )
        
        # Validate result_format is one of the allowed values
        valid_formats = ["True/False", "Text", "Number"]
        if enrichment.result_format and enrichment.result_format not in valid_formats:
            return (
                False,
                f"Invalid result format '{enrichment.result_format}'. Must be one of: {', '.join(valid_formats)}",
                None
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
            return (False, error_msg, missing_fields)
        
        return (True, None, None)

    def create_enrichment(self, 
        project_id: int,
        enrichment_name: str,
        column_name: Optional[str] = None,
        enrichment_description: Optional[str] = None) -> Enrichment:
        """Create a new enrichment for a project"""
        try:
            with db_service.get_session() as session:
                # Check if enrichment name already exists for this project
                existing_enrichment = session.query(Enrichment).filter(
                    Enrichment.project_id == project_id,
                    Enrichment.enrichment_name == enrichment_name
                ).first()
                if existing_enrichment:
                    raise DuplicateEnrichmentNameError(enrichment_name)
                
                # Check if column name already exists for this project (only if provided)
                if column_name:
                    existing_column = session.query(Enrichment).filter(
                        Enrichment.project_id == project_id,
                        Enrichment.column_name == column_name
                    ).first()
                    if existing_column:
                        raise DuplicateColumnNameError(column_name)
                
                enrichment = Enrichment(
                    project_id=project_id,
                    enrichment_name=enrichment_name,
                    column_name=column_name,
                    enrichment_description=enrichment_description
                )
                session.add(enrichment)
                session.commit()
                session.refresh(enrichment)
                if column_name:
                    logger.info(f"✅ Created enrichment: {enrichment_name} (column: {column_name}) for project {project_id}")
                else:
                    logger.info(f"✅ Created enrichment: {enrichment_name} (column name to be set later) for project {project_id}")
                return enrichment
        except IntegrityError as e:
            # Handle unique constraint violation
            if "uq_enrichments_project_name" in str(e.orig):
                raise DuplicateEnrichmentNameError(enrichment_name)
            elif "uq_enrichments_project_column" in str(e.orig):
                raise DuplicateColumnNameError(column_name)
            raise
        except SQLAlchemyError as e:
            logger.exception("❌ Error creating enrichment")
            raise DatabaseFailureError("Failed to create enrichment") from e
    
    def get_enrichments(self, project_id: int) -> List[Enrichment]:
        """Get all enrichments for a project"""
        try:
            with db_service.get_session() as session:
                return session.query(Enrichment).filter(
                    Enrichment.project_id == project_id
                ).order_by(Enrichment.date_added.desc()).all()
        except SQLAlchemyError as e:
            logger.exception("❌ Error getting enrichments")
            raise DatabaseFailureError("Failed to retrieve enrichments") from e
    
    def get_enrichment(self, enrichment_id: int) -> Optional[Enrichment]:
        """Get specific enrichment by ID"""
        try:
            with db_service.get_session() as session:
                enrichment = session.query(Enrichment).filter(Enrichment.id == enrichment_id).first()
                if not enrichment:
                    raise EnrichmentNotFoundError(enrichment_id)
                return enrichment
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error getting enrichment {enrichment_id}")
            raise DatabaseFailureError(f"Failed to retrieve enrichment {enrichment_id}") from e
    
    def update_enrichment(self, enrichment_id: int, **kwargs) -> Optional[Enrichment]:
        """Update enrichment fields"""
        try:
            with db_service.get_session() as session:
                enrichment = session.query(Enrichment).filter(Enrichment.id == enrichment_id).first()
                if not enrichment:
                    raise EnrichmentNotFoundError(enrichment_id)
                
                # Check if enrichment_name is being updated and if it already exists for this project
                if 'enrichment_name' in kwargs:
                    new_enrichment_name = kwargs['enrichment_name']
                    # Only check for duplicates if the name is actually changing
                    if new_enrichment_name != enrichment.enrichment_name:
                        existing_enrichment = session.query(Enrichment).filter(
                            Enrichment.project_id == enrichment.project_id,
                            Enrichment.enrichment_name == new_enrichment_name,
                            Enrichment.id != enrichment_id
                        ).first()
                        if existing_enrichment:
                            raise DuplicateEnrichmentNameError(new_enrichment_name)
                
                # Check if column_name is being updated and if it already exists for this project
                if 'column_name' in kwargs:
                    new_column_name = kwargs['column_name']
                    # Only check for duplicates if the name is actually changing
                    if new_column_name != enrichment.column_name:
                        existing_column = session.query(Enrichment).filter(
                            Enrichment.project_id == enrichment.project_id,
                            Enrichment.column_name == new_column_name,
                            Enrichment.id != enrichment_id
                        ).first()
                        if existing_column:
                            raise DuplicateColumnNameError(new_column_name)
                
                for key, value in kwargs.items():
                    if hasattr(enrichment, key):
                        setattr(enrichment, key, value)
                
                session.commit()
                session.refresh(enrichment)
                logger.info(f"✅ Updated enrichment {enrichment_id}")
                return enrichment
        except IntegrityError as e:
            # Handle unique constraint violation
            if "uq_enrichments_project_name" in str(e.orig):
                if 'enrichment_name' in kwargs:
                    raise DuplicateEnrichmentNameError(kwargs['enrichment_name'])
            raise
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error updating enrichment {enrichment_id}")
            raise DatabaseFailureError(f"Failed to update enrichment {enrichment_id}") from e
    
    def delete_enrichment(self, enrichment_id: int) -> None:
        """Delete enrichment by ID"""
        try:
            with db_service.get_session() as session:
                enrichment = session.query(Enrichment).filter(Enrichment.id == enrichment_id).first()
                if not enrichment:
                    raise EnrichmentNotFoundError(enrichment_id)
                
                session.delete(enrichment)
                session.commit()
                logger.info(f"✅ Deleted enrichment {enrichment_id}")
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error deleting enrichment {enrichment_id}")
            raise DatabaseFailureError(f"Failed to delete enrichment {enrichment_id}") from e

    async def process_leads_enrichment(
        self,
        enrichment: Enrichment,
        leads_data: List[Dict[str, Any]],
        column_name: str,
        enrichment_execution_service
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Process leads enrichment using the enrichment configuration.
        
        Args:
            enrichment: The enrichment configuration
            leads_data: List of lead dictionaries
            column_name: Column name for the enrichment output
            enrichment_execution_service: Service to execute the enrichment
            
        Returns:
            Tuple of (enriched_leads, columns)
        """
        # Map result_format to output_type for AI service
        output_type_map = {
            "True/False": "bool",
            "Text": "str",
            "Number": "int"
        }
        output_type = output_type_map.get(enrichment.result_format)
        
        # Process each lead
        enriched_leads = []
        for lead_row in leads_data:
            company_name = lead_row.get("lead", "")
            if not company_name:
                # Skip leads without a "lead" field
                continue
            
            try:
                # Run enrichment for this company
                result = await enrichment_execution_service.enrich_company(
                    company_name=company_name,
                    enrichment_name=column_name,
                    prompt_goal=enrichment.goal,
                    prompt_reasoning=enrichment.acceptable_evidence,
                    output_type=output_type,
                    string_prompt=enrichment.result_text_value or "",
                    is_false_prompt=enrichment.result_false_if or "",
                    is_true_prompt=enrichment.result_true_if or "",
                    int_prompt=enrichment.result_number_value or "",
                    return_metadata=False
                )
                
                # Create enriched lead row
                enriched_lead = lead_row.copy()
                
                # Extract the enrichment value, reasoning, and evidence from result
                enrichment_value = result.get(column_name)
                enrichment_reasoning = result.get(f"{column_name}_reasoning", "")
                enrichment_evidence = result.get(f"{column_name}_evidence", "")
                
                enriched_lead[column_name] = enrichment_value
                enriched_lead[f"{column_name}_reasoning"] = enrichment_reasoning
                enriched_lead[f"{column_name}_evidence"] = enrichment_evidence
                
                enriched_leads.append(enriched_lead)
                
            except (ExternalScraperError, OpenAITokenLimitExceededError, ApiKeyNotConfiguredError,
                    TimeoutError, openai.APITimeoutError, openai.RateLimitError, 
                    openai.BadRequestError, RuntimeError) as e:
                # Known external API errors and retryable failures - continue processing other leads
                # Note: Programming errors (KeyError, TypeError, AttributeError, etc.) are NOT caught
                # They will propagate up to indicate bugs that need fixing
                logger.exception(
                    f"❌ Failed to enrich '{company_name}' for column '{column_name}'. "
                    f"Error: {type(e).__name__}: {str(e)}"
                )
                
                # Add the lead with NULL values - keep business data clean
                # Error details are in logs, not in business data
                enriched_lead = lead_row.copy()
                enriched_lead[column_name] = None
                enriched_lead[f"{column_name}_reasoning"] = None
                enriched_lead[f"{column_name}_evidence"] = None
                enriched_leads.append(enriched_lead)
        
        # Get columns list
        columns = list(enriched_leads[0].keys()) if enriched_leads else ["lead"]
        # Ensure enrichment columns are in the list
        if column_name not in columns:
            columns.append(column_name)
        if f"{column_name}_reasoning" not in columns:
            columns.append(f"{column_name}_reasoning")
        if f"{column_name}_evidence" not in columns:
            columns.append(f"{column_name}_evidence")
        
        return (enriched_leads, columns)

# Global enrichment service instance
enrichment_service = EnrichmentService()

