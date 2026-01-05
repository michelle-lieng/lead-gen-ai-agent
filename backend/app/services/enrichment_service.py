"""
Enrichment service for managing enrichment operations
"""

from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import logging

from .database_service import db_service

from ..models.tables import Enrichment
from ..exceptions import (
    DuplicateEnrichmentNameError,
    DuplicateEnrichmentColumnNameError,
    EnrichmentNotFoundError,
    DatabaseFailureError,
    EmptyEnrichmentFieldError,
    IncompleteEnrichmentConfigError,
)

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Service for enrichment-related database operations"""

    def _validate_enrichment_update(
        self, enrichment: Enrichment, update_data: dict
    ) -> None:
        """
        Validate enrichment update business rules.

        Rules:
        1. Core fields cannot be empty (except enrichment_description)
        2. Format-specific fields must be filled based on result_format

        Args:
            enrichment: The existing enrichment from DB
            update_data: The fields being updated

        Raises:
            EmptyEnrichmentFieldError: If a required field is being set to empty
            IncompleteEnrichmentConfigError: If format-specific fields are missing
        """
        # Fields that cannot be empty when updated (except enrichment_description)
        core_fields = [
            "enrichment_name",
            "column_name",
            "goal",
            "acceptable_evidence",
            "result_format",
        ]

        # Check that core fields being updated are not empty
        empty_fields = []
        for field in core_fields:
            if field in update_data:
                value = update_data[field]
                if value is not None and (
                    not isinstance(value, str) or not value.strip()
                ):
                    empty_fields.append(field)

        if empty_fields:
            raise EmptyEnrichmentFieldError(empty_fields)

        # Get the result_format (from update or from DB)
        result_format = update_data.get("result_format", enrichment.result_format)

        # Only validate format-specific fields if result_format is set
        if result_format:
            missing_fields = []

            if result_format == "True/False":
                # Check result_true_if (from update or DB)
                true_if_value = update_data.get(
                    "result_true_if", enrichment.result_true_if
                )
                if not true_if_value or not true_if_value.strip():
                    missing_fields.append("result_true_if")

                # Check result_false_if (from update or DB)
                false_if_value = update_data.get(
                    "result_false_if", enrichment.result_false_if
                )
                if not false_if_value or not false_if_value.strip():
                    missing_fields.append("result_false_if")

            elif result_format == "Number":
                # Check result_number_value (from update or DB)
                number_value = update_data.get(
                    "result_number_value", enrichment.result_number_value
                )
                if not number_value or not number_value.strip():
                    missing_fields.append("result_number_value")

            elif result_format == "Text":
                # Check result_text_value (from update or DB)
                text_value = update_data.get(
                    "result_text_value", enrichment.result_text_value
                )
                if not text_value or not text_value.strip():
                    missing_fields.append("result_text_value")

            if missing_fields:
                raise IncompleteEnrichmentConfigError(result_format, missing_fields)

    def create_enrichment(
        self,
        project_id: int,
        enrichment_name: str,
        enrichment_description: Optional[str] = None,
    ) -> Enrichment:
        """Create a new enrichment for a project"""
        try:
            with db_service.get_session() as session:
                # Check if enrichment name already exists for this project
                existing_enrichment = (
                    session.query(Enrichment)
                    .filter(
                        Enrichment.project_id == project_id,
                        Enrichment.enrichment_name == enrichment_name,
                    )
                    .first()
                )
                if existing_enrichment:
                    raise DuplicateEnrichmentNameError(enrichment_name)

                enrichment = Enrichment(
                    project_id=project_id,
                    enrichment_name=enrichment_name,
                    enrichment_description=enrichment_description,
                )
                session.add(enrichment)
                session.commit()
                session.refresh(enrichment)
                logger.info(
                    f"✅ Created enrichment: {enrichment_name} for project {project_id}"
                )
                return enrichment
        except SQLAlchemyError as e:
            logger.exception("❌ Error creating enrichment")
            raise DatabaseFailureError("Failed to create enrichment") from e

    def get_enrichments(self, project_id: int) -> list[Enrichment]:
        """Get all enrichments for a project"""
        try:
            with db_service.get_session() as session:
                return (
                    session.query(Enrichment)
                    .filter(Enrichment.project_id == project_id)
                    .order_by(Enrichment.date_added.desc())
                    .all()
                )
        except SQLAlchemyError as e:
            logger.exception("❌ Error getting enrichments")
            raise DatabaseFailureError("Failed to retrieve enrichments") from e

    def get_enrichment(self, enrichment_id: int) -> Enrichment:
        """Get specific enrichment by ID"""
        try:
            with db_service.get_session() as session:
                enrichment = (
                    session.query(Enrichment)
                    .filter(Enrichment.id == enrichment_id)
                    .first()
                )
                if not enrichment:
                    raise EnrichmentNotFoundError(enrichment_id)
                return enrichment
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error getting enrichment {enrichment_id}")
            raise DatabaseFailureError(
                f"Failed to retrieve enrichment {enrichment_id}"
            ) from e

    def update_enrichment(self, enrichment_id: int, **kwargs) -> Enrichment:
        """Update enrichment fields"""
        try:
            with db_service.get_session() as session:
                enrichment = (
                    session.query(Enrichment)
                    .filter(Enrichment.id == enrichment_id)
                    .first()
                )
                if not enrichment:
                    raise EnrichmentNotFoundError(enrichment_id)

                # Validate business rules before updating
                self._validate_enrichment_update(enrichment, kwargs)

                # Check if enrichment_name is being updated and if it already exists for this project
                if "enrichment_name" in kwargs:
                    new_enrichment_name = kwargs["enrichment_name"]
                    # Only check for duplicates if the name is actually changing
                    if new_enrichment_name != enrichment.enrichment_name:
                        existing_enrichment = (
                            session.query(Enrichment)
                            .filter(
                                Enrichment.project_id == enrichment.project_id,
                                Enrichment.enrichment_name == new_enrichment_name,
                                Enrichment.id != enrichment_id,
                            )
                            .first()
                        )
                        if existing_enrichment:
                            raise DuplicateEnrichmentNameError(new_enrichment_name)

                # Check if column_name is being updated and if it already exists for this project
                if "column_name" in kwargs:
                    new_column_name = kwargs["column_name"]
                    # Only check for duplicates if the name is actually changing
                    if new_column_name != enrichment.column_name:
                        existing_column = (
                            session.query(Enrichment)
                            .filter(
                                Enrichment.project_id == enrichment.project_id,
                                Enrichment.column_name == new_column_name,
                                Enrichment.id != enrichment_id,
                            )
                            .first()
                        )
                        if existing_column:
                            raise DuplicateEnrichmentColumnNameError(new_column_name)

                for key, value in kwargs.items():
                    if hasattr(enrichment, key):
                        setattr(enrichment, key, value)

                session.commit()
                session.refresh(enrichment)
                logger.info(f"✅ Updated enrichment {enrichment_id}")
                return enrichment
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error updating enrichment {enrichment_id}")
            raise DatabaseFailureError(
                f"Failed to update enrichment {enrichment_id}"
            ) from e

    def delete_enrichment(self, enrichment_id: int) -> None:
        """Delete enrichment by ID"""
        try:
            with db_service.get_session() as session:
                enrichment = (
                    session.query(Enrichment)
                    .filter(Enrichment.id == enrichment_id)
                    .first()
                )
                if not enrichment:
                    raise EnrichmentNotFoundError(enrichment_id)

                session.delete(enrichment)
                session.commit()
                logger.info(f"✅ Deleted enrichment {enrichment_id}")
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error deleting enrichment {enrichment_id}")
            raise DatabaseFailureError(
                f"Failed to delete enrichment {enrichment_id}"
            ) from e


# Global enrichment service instance
enrichment_service = EnrichmentService()
