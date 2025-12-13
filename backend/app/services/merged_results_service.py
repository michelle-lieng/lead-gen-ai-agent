"""
Merged results service for combining SERP leads and dataset leads
"""
import logging
import re
import csv
import zipfile
from io import StringIO, BytesIO
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import json

from .database_service import db_service
from .project_service import project_service
from ..models.tables import SerpLeadAggregated, Dataset, ProjectDataset, MergedResult
from ..utils.lead_utils import normalize_lead_name, sanitize_value
from ..exceptions import InvalidEnrichmentColumnError, DatabaseFailureError, ProjectNotFoundError, ProjectDatasetNotFoundError

logger = logging.getLogger(__name__)


class MergedResultsService:
    """Service for merging SERP leads and dataset leads into merged_results table"""

    def _ensure_enrichment_column_exists(self, column_name: str, dataset_name: str) -> str:
        """
        Ensure an enrichment column exists in merged_results table.
        Adds the column if it doesn't exist.
        Prefixes the column name with dataset name to avoid conflicts:
        e.g., "dataset_name_mandate" instead of just "mandate"
        
        Note: Rows are isolated by project_id, so even if multiple projects use the same
        column name, there's no conflict since updates only affect rows with that project_id.
        
        Args:
            column_name: Name of the enrichment column to ensure exists
            dataset_name: Dataset name to prefix the column with (required)
            
        Returns:
            str: The final sanitized column name (with dataset name prefix)
            
        Raises:
            InvalidEnrichmentColumnError: If column name or dataset name is invalid after sanitization
            DatabaseFailureError: If database operation fails
        """
        # Sanitize column name
        safe_column_name = sanitize_value(column_name)
        if not safe_column_name:
            raise InvalidEnrichmentColumnError(f"Invalid column name: '{column_name}' (became empty after sanitization)")
        
        # Sanitize and validate dataset name
        safe_dataset_name = sanitize_value(dataset_name)
        if not safe_dataset_name:
            raise InvalidEnrichmentColumnError(f"Invalid dataset name: '{dataset_name}' (became empty after sanitization)")
        
        # Check if column name already starts with dataset name prefix (e.g., "dataset_name_exists")
        if safe_column_name.startswith(f"{safe_dataset_name}_"):
            # Already prefixed (e.g., "dataset_name_exists"), use as-is
            final_column_name = safe_column_name
        else:
            # Not prefixed, add dataset name prefix
            final_column_name = f"{safe_dataset_name}_{safe_column_name}"
        
        try:
            with db_service.get_session() as session:
                # Check if column exists
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'merged_results' 
                    AND column_name = :column_name
                """)
                result = session.execute(check_query, {"column_name": final_column_name}).fetchone()
                
                if result:
                    # Column already exists
                    return final_column_name
                
                # Add column if it doesn't exist
                alter_query = text(f"""
                    ALTER TABLE merged_results 
                    ADD COLUMN {final_column_name} TEXT
                """)
                session.execute(alter_query)
                session.commit()
                
                logger.info(f"✅ Added enrichment column '{final_column_name}' to merged_results table")
                return final_column_name
                
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error ensuring enrichment column '{column_name}' exists")
            raise DatabaseFailureError(f"Failed to ensure enrichment column '{column_name}' exists") from e

    def merge_serp_leads(self, project_id: int) -> dict:
        """
        Merge aggregated SERP leads into merged_results table.
        Called after SERP aggregation completes.
        
        Strategy: Refresh SERP data by:
        1. Setting all existing merged_results serp_count to NULL (preserve enrichment columns)
        2. Insert/update with latest SERP counts from aggregated leads
        This ensures we always have the latest SERP counts without losing enrichment data.
        
        Args:
            project_id: Project ID to merge leads for
            
        Returns:
            dict: Success status and statistics
        """
        try:
            with db_service.get_session() as session:
                # Get all aggregated SERP leads for this project
                aggregated_leads = session.query(SerpLeadAggregated).filter(
                    SerpLeadAggregated.project_id == project_id
                ).all()
                
                if not aggregated_leads:
                    logger.info(f"No aggregated SERP leads found for project {project_id} to merge")
                    # Clear SERP counts for existing records (they may have been removed)
                    session.query(MergedResult).filter(
                        MergedResult.project_id == project_id
                    ).update({"serp_count": None})
                    session.commit()
                    return {
                        "success": True,
                        "leads_merged": 0,
                        "message": "No aggregated SERP leads found to merge"
                    }
                
                # Step 1: Reset all SERP counts to NULL (preserve enrichment columns)
                # This handles cases where leads were removed from SERP results
                session.query(MergedResult).filter(
                    MergedResult.project_id == project_id
                ).update({"serp_count": None})
                
                merged_count = 0
                updated_count = 0
                
                # Step 2: Insert or update with latest SERP counts
                for agg_lead in aggregated_leads:
                    # Normalize lead name (already normalized in aggregation, but ensure consistency)
                    normalized_lead = normalize_lead_name(agg_lead.leads)
                    
                    if not normalized_lead:
                        continue
                    
                    # Check if lead already exists in merged_results
                    existing = session.query(MergedResult).filter(
                        MergedResult.project_id == project_id,
                        MergedResult.lead == normalized_lead
                    ).first()
                    
                    if existing:
                        # Update existing record with latest SERP count
                        existing.serp_count = agg_lead.serp_count
                        updated_count += 1
                    else:
                        # Create new merged result (only SERP data, no enrichment yet)
                        merged_result = MergedResult(
                            project_id=project_id,
                            lead=normalized_lead,
                            serp_count=agg_lead.serp_count
                        )
                        session.add(merged_result)
                        merged_count += 1
                
                session.commit()
                
                total_processed = merged_count + updated_count
                logger.info(f"✅ Merged {total_processed} SERP leads for project {project_id} ({merged_count} new, {updated_count} updated)")
                
                return {
                    "success": True,
                    "leads_merged": merged_count,
                    "leads_updated": updated_count,
                    "total_processed": total_processed,
                    "message": f"Merged {total_processed} SERP leads ({merged_count} new, {updated_count} updated)"
                }
                
        except SQLAlchemyError as e:
            logger.exception("❌ Database error merging SERP leads")
            raise DatabaseFailureError("Failed to merge SERP leads") from e

    def merge_dataset_leads(self, project_id: int, project_dataset_id: int, enrichment_column_list: list[str]) -> dict:
        """
        Merge dataset leads into merged_results table.
        Adds enrichment column(s) dynamically if they don't exist.
        Enrichment columns are prefixed with dataset name to avoid conflicts:
        e.g., "dataset_name_mandate" instead of just "mandate"
        
        Args:
            project_id: Project ID to merge leads for
            project_dataset_id: ProjectDataset ID that was just uploaded
            enrichment_column_list: List of enrichment column name(s)
            
        Returns:
            dict: Success status and statistics
        """
        try:
            with db_service.get_session() as session:
                # Get ProjectDataset to retrieve dataset name for column prefixing
                project_dataset = session.query(ProjectDataset).filter(
                    ProjectDataset.id == project_dataset_id
                ).first()
                
                if not project_dataset:
                    raise ProjectDatasetNotFoundError(project_dataset_id)
                
                # Build prefixed enrichment column names: {dataset_name}_{column_name}
                # The _ensure_enrichment_column_exists method handles prefixing automatically
                prefixed_enrichment_columns = {}
                prefixed_column_names = []
                for col in enrichment_column_list:
                    prefixed_name = self._ensure_enrichment_column_exists(col, dataset_name=project_dataset.dataset_name)
                    prefixed_enrichment_columns[col] = prefixed_name
                    prefixed_column_names.append(prefixed_name)
                
                # Store the prefixed column names in ProjectDataset for efficient retrieval later
                project_dataset.enrichment_column_list = ",".join(prefixed_column_names)
                session.flush()  # Save the updated prefixed names
                
                # Get all dataset rows for this project_dataset
                dataset_rows = session.query(Dataset).filter(
                    Dataset.project_dataset_id == project_dataset_id
                ).all()
                
                if not dataset_rows:
                    logger.info(f"No dataset rows found for project_dataset {project_dataset_id} to merge")
                    return {
                        "success": True,
                        "leads_merged": 0,
                        "message": "No dataset rows found to merge"
                    }
                
                merged_count = 0
                updated_count = 0
                
                for dataset_row in dataset_rows:
                    # Normalize lead name
                    normalized_lead = normalize_lead_name(dataset_row.lead)
                    
                    if not normalized_lead:
                        continue
                    
                    # Check if lead already exists in merged_results
                    existing = session.query(MergedResult).filter(
                        MergedResult.project_id == project_id,
                        MergedResult.lead == normalized_lead
                    ).first()
                    
                    # Parse enrichment value(s)
                    if len(enrichment_column_list) == 1:
                        # Single column - use value directly
                        original_col_name = enrichment_column_list[0]
                        enrichment_values = {original_col_name: str(dataset_row.enrichment_value) if dataset_row.enrichment_value else None}
                    else:
                        # Multiple columns - parse JSON
                        try:
                            enrichment_values = json.loads(dataset_row.enrichment_value) if dataset_row.enrichment_value else {}
                        except:
                            enrichment_values = {}
                    
                    if existing:
                        # Update existing record with enrichment value(s)
                        # Use prefixed column names for database updates
                        for original_col_name, col_value in enrichment_values.items():
                            prefixed_column_name = prefixed_enrichment_columns[original_col_name]
                            update_query = text(f"""
                                UPDATE merged_results 
                                SET {prefixed_column_name} = :enrichment_value
                                WHERE id = :id
                            """)
                            session.execute(update_query, {
                                "enrichment_value": col_value,
                                "id": existing.id
                            })
                        updated_count += 1
                    else:
                        # Create new merged result
                        # First insert with fixed columns
                        merged_result = MergedResult(
                            project_id=project_id,
                            lead=normalized_lead,
                            serp_count=0  # No SERP data yet
                        )
                        session.add(merged_result)
                        session.flush()  # Get the ID
                        
                        # Then update the dynamic enrichment column(s)
                        # Use prefixed column names for database updates
                        for original_col_name, col_value in enrichment_values.items():
                            prefixed_column_name = prefixed_enrichment_columns[original_col_name]
                            update_query = text(f"""
                                UPDATE merged_results 
                                SET {prefixed_column_name} = :enrichment_value
                                WHERE id = :id
                            """)
                            session.execute(update_query, {
                                "enrichment_value": col_value,
                                "id": merged_result.id
                            })
                        
                        merged_count += 1
                
                session.commit()
                
                total_processed = merged_count + updated_count
                logger.info(f"✅ Merged {total_processed} dataset leads for project {project_id} ({merged_count} new, {updated_count} updated)")
                
                return {
                    "success": True,
                    "leads_merged": merged_count,
                    "leads_updated": updated_count,
                    "total_processed": total_processed,
                    "message": f"Merged {total_processed} dataset leads ({merged_count} new, {updated_count} updated)"
                }
                
        except SQLAlchemyError as e:
            logger.exception("❌ Database error merging dataset leads")
            raise DatabaseFailureError("Failed to merge dataset leads") from e

    def _get_project_enrichment_columns(self, session, project_id: int) -> list[str]:
        """
        Get list of enrichment column names that belong to this project.
        These are the prefixed columns created from datasets uploaded to this project.
        
        Efficient approach: Read prefixed column names directly from ProjectDataset records,
        which are stored when datasets are merged.
        
        Args:
            session: Database session
            project_id: Project ID to get enrichment columns for
            
        Returns:
            list[str]: List of enrichment column names (prefixed with dataset names)
        """
        # Get all ProjectDataset records for this project and extract prefixed column names
        project_datasets = session.query(ProjectDataset).filter(
            ProjectDataset.project_id == project_id
        ).all()
        
        # Parse comma-separated prefixed column names from each dataset
        enrichment_columns = [
            col.strip()
            for project_dataset in project_datasets
            for col in project_dataset.enrichment_column_list.split(',')
        ]
        
        return enrichment_columns
    
    def get_merged_results(self, project_id: int) -> dict:
        """
        Get merged_results table as list of dictionaries (JSON-friendly).
        Only includes enrichment columns that belong to this project.
        
        Args:
            project_id: Project ID to get merged results for
            
        Returns:
            dict: Dictionary with 'data' (list of dicts) and 'columns' (list of column names)
        """
        try:
            with db_service.get_session() as session:
                # Base columns that always exist
                base_columns = ['lead', 'serp_count']
                
                # Get enrichment columns that belong to this project
                enrichment_columns = self._get_project_enrichment_columns(session, project_id)
                
                # Combine base columns and project-specific enrichment columns
                column_names = base_columns + enrichment_columns
                
                # Get all merged results for this project using raw SQL
                columns_str = ", ".join([f'"{col}"' for col in column_names])
                
                select_query = text(f"""
                    SELECT {columns_str}
                    FROM merged_results
                    WHERE project_id = :project_id
                """)
                
                results = session.execute(select_query, {"project_id": project_id}).fetchall()
                
                if not results:
                    return {"data": [], "columns": column_names, "count": 0}
                
                # Convert to list of dictionaries
                data = []
                for row_data in results:
                    row_dict = {}
                    for idx, col_name in enumerate(column_names):
                        value = row_data[idx]
                        
                        # Format the value for JSON
                        if value is None:
                            row_dict[col_name] = None
                        elif isinstance(value, datetime):
                            row_dict[col_name] = value.isoformat()
                        else:
                            row_dict[col_name] = value
                    
                    data.append(row_dict)
                
                logger.info(f"✅ Retrieved {len(data)} merged results for project {project_id}")
                
                return {"data": data, "columns": column_names, "count": len(data)}
                
        except SQLAlchemyError as e:
            logger.exception("❌ Database error getting merged results")
            raise DatabaseFailureError("Failed to get merged results") from e

    def _export_merged_results_as_csv(self, project_id: int) -> dict:
        """
        Export merged_results table as CSV for a project.
        Only includes enrichment columns that belong to this project.
        
        Args:
            project_id: Project ID to export merged results for
            
        Returns:
            dict: Dictionary with CSV content as string
        """
        try:
            with db_service.get_session() as session:
                # Base columns (exclude id and project_id for export)
                base_columns = ['lead', 'serp_count']
                
                # Get enrichment columns that belong to this project
                enrichment_columns = self._get_project_enrichment_columns(session, project_id)
                
                # Combine base columns and project-specific enrichment columns
                all_column_names = base_columns + enrichment_columns
                column_names = all_column_names  # For export, we want all of these
                
                # Get all merged results for this project using raw SQL
                columns_str = ", ".join([f'"{col}"' for col in all_column_names])
                
                select_query = text(f"""
                    SELECT {columns_str}
                    FROM merged_results
                    WHERE project_id = :project_id
                """)
                
                results = session.execute(select_query, {"project_id": project_id}).fetchall()
                
                if not results:
                    return {"csv_content": None, "row_count": 0, "message": "No merged results found for this project"}
                
                # Create CSV
                output = StringIO()
                writer = csv.writer(output)
                
                # Write header row (only non-excluded columns)
                writer.writerow(column_names)
                
                # Create mapping from all columns to export columns
                column_indices = {col: idx for idx, col in enumerate(all_column_names)}
                export_indices = [column_indices[col] for col in column_names]
                
                # Write data rows
                for row_data in results:
                    row = []
                    for idx in export_indices:
                        value = row_data[idx]
                        
                        # Format the value
                        if value is None:
                            row.append("")
                        elif isinstance(value, datetime):
                            row.append(value.isoformat())
                        else:
                            row.append(str(value))
                    
                    writer.writerow(row)
                
                csv_content = output.getvalue()
                
                logger.info(f"✅ Exported {len(results)} merged results for project {project_id}")
                
                return {"csv_content": csv_content, "row_count": len(results)}
                
        except SQLAlchemyError as e:
            logger.exception("❌ Database error exporting merged results as CSV")
            raise DatabaseFailureError("Failed to export merged results as CSV") from e

    def export_merged_results_as_zip(self, project_id: int) -> tuple[bytes | None, str | None]:
        """
        Export merged_results table as a ZIP file containing CSV.
        
        Args:
            project_id: Project ID to export merged results for
            
        Returns:
            tuple[bytes | None, str | None]: 
                - zip_file_bytes: Binary content of the ZIP file, or None if no data to download
                - filename: Suggested filename for download, or None if no data to download
                Returns (None, None) when there are no merged results to download (should return 204)
                
        Raises:
            ProjectNotFoundError: If project doesn't exist (from project_service.get_project)
        """
        try:
            # Step 1: Get CSV data
            export_result = self._export_merged_results_as_csv(project_id)
            csv_content = export_result.get("csv_content")
            
            # Step 2: Check if there's data to download
            if not csv_content or export_result.get("row_count", 0) == 0:
                # No data to download - return None to signal 204 response
                return None, None
            
            # Step 3: Generate timestamp for filename
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Step 4: Get project name for meaningful filename
            project = project_service.get_project(project_id)
            if not project:
                raise ProjectNotFoundError(project_id)
            project_name = project.project_name
            
            # Step 5: Sanitize project name for filename
            safe_project_name = re.sub(r'[^\w\s-]', '', project_name).strip().replace(' ', '_')
            
            # Step 6: Generate ZIP filename
            zip_filename = f"{safe_project_name}_merged_results_{timestamp_str}.zip"
            
            # Step 7: Create ZIP file in memory
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Encode CSV with UTF-8 BOM for Excel compatibility
                zip_file.writestr("merged_results.csv", csv_content.encode('utf-8-sig'))
            
            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()
            
            logger.info(f"✅ Generated merged results ZIP file for project {project_id}: {zip_filename} ({len(zip_bytes)} bytes)")
            
            return zip_bytes, zip_filename
        except SQLAlchemyError as e:
            logger.exception("❌ Database error exporting merged results as ZIP")
            raise DatabaseFailureError("Failed to export merged results as ZIP") from e

# Global service instance
merged_results_service = MergedResultsService()

