"""
Dataset upload and management service
"""
import logging
import pandas as pd
import csv
import re
import json
from io import BytesIO, StringIO
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from .database_service import db_service
from .project_service import project_service
from ..models.tables import ProjectDataset, Dataset, Project
from .merged_results_service import merged_results_service
from ..utils.lead_utils import normalize_lead_name, sanitize_value

logger = logging.getLogger(__name__)


class LeadsDatasetService:
    """Service for managing dataset uploads and processing"""

    def upload_dataset(
        self,
        project_id: int,
        dataset_name: str,
        lead_column: str,
        enrichment_column_list: list[str],  # Always a list (empty if no enrichment columns)
        enrichment_column_exists: bool,
        csv_content: bytes  # CSV file as bytes
    ) -> dict:
        """
        Upload and process a CSV dataset.
        
        Args:
            project_id: Project ID to link dataset to
            dataset_name: User-friendly name for the dataset
            lead_column: Name of column containing leads (company names)
            enrichment_column_list: Name of column(s) for enrichment values in list
            enrichment_column_exists: Whether the enrichment column exists in CSV
            csv_content: CSV file content as bytes
            
        Returns:
            dict: Success status and statistics
        """
        try:
            with db_service.get_session() as session:
                # Validate project exists
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project {project_id} not found")
                
                # Parse CSV
                # csv_content is always bytes from FastAPI UploadFile.read()
                try:
                    df = pd.read_csv(BytesIO(csv_content), encoding='utf-8', encoding_errors='replace')
                except Exception as e:
                    raise ValueError(f"Failed to parse CSV file: {str(e)}")
                
                # Normalize column names (strip whitespace)
                df.columns = df.columns.str.strip()
                lead_column = lead_column.strip()
                enrichment_column_list = [col.strip() for col in enrichment_column_list]
                
                # Validate lead_column exists
                if lead_column not in df.columns:
                    raise ValueError(f"Lead column '{lead_column}' not found in CSV. Available columns: {', '.join(df.columns)}")
                
                # Handle enrichment columns (can be single or multiple)
                if enrichment_column_exists:
                    # User selected columns from CSV - verify they all exist
                    if len(enrichment_column_list) == 0:
                        raise ValueError("enrichment_column_list cannot be empty when enrichment_column_exists is True")
                    
                    missing_columns = [col for col in enrichment_column_list if col not in df.columns]
                    if missing_columns:
                        raise ValueError(
                            f"Enrichment column(s) not found in CSV: {', '.join(missing_columns)}. "
                            f"Available columns: {', '.join(df.columns)}"
                        )
    
                    enrichment_column_for_merge = enrichment_column_list
                    logger.info(f"Using {len(enrichment_column_list)} enrichment column(s) from CSV: {', '.join(enrichment_column_list)}")
                else:
                    # Single enrichment column - will be created with value True
                    safe_dataset_name = sanitize_value(dataset_name)
                    enrichment_column_for_merge = [f"{safe_dataset_name}_exists"]
                    logger.info(f"Creating column '{safe_dataset_name}_exists' with value True")
                
                # Check for duplicate leads in the CSV (case-insensitive, whitespace-trimmed)
                lead_values = df[lead_column].astype(str).str.strip()
                # Remove empty/NaN values for duplicate check
                non_empty_leads = lead_values[lead_values != ''].str.lower()
                duplicates = non_empty_leads[non_empty_leads.duplicated(keep=False)]
                
                if not duplicates.empty:
                    # Get unique duplicate lead names (original case from first occurrence)
                    duplicate_leads = []
                    seen_lower = set()
                    for idx, lead_lower in duplicates.items():
                        if lead_lower not in seen_lower:
                            seen_lower.add(lead_lower)
                            # Get original case from dataframe
                            original_lead = str(df.loc[idx, lead_column]).strip()
                            duplicate_leads.append(original_lead)
                    
                    raise ValueError(
                        f"Duplicate leads found in CSV. Each lead must be unique. "
                        f"Found duplicates: {', '.join(duplicate_leads[:10])}"
                        f"{'...' if len(duplicate_leads) > 10 else ''}"
                    )
                
                # Create ProjectDataset record
                project_dataset = ProjectDataset(
                    project_id=project_id,
                    dataset_name=dataset_name,
                    lead_column=lead_column,
                    enrichment_column_list=",".join(enrichment_column_for_merge),  # Store as comma-separated string in DB
                    row_count=0  # Will update after processing
                )
                session.add(project_dataset)
                session.flush()  # Get the ID without committing yet
                
                # Process rows
                rows_processed = 0
                
                for idx, row in df.iterrows():
                    try:
                        # Get lead value and normalize it (lowercase, trim whitespace, etc.)
                        lead_value = str(row[lead_column]).strip()
                        if not lead_value or pd.isna(row[lead_column]):
                            logger.warning(f"Skipping row {idx}: empty lead value")
                            continue
                        
                        # Normalize lead name before saving (lowercase, trim whitespace)
                        normalized_lead = normalize_lead_name(lead_value)
                        
                        # Skip empty leads after normalization
                        if not normalized_lead:
                            logger.warning(f"Skipping row {idx}: lead became empty after normalization")
                            continue
                        
                        # Get enrichment value(s)
                        if enrichment_column_exists and len(enrichment_column_list) > 0:
                            # Multiple or single enrichment columns from CSV
                            if len(enrichment_column_list) == 1:
                                # Single column - store value directly
                                enrichment_value = str(row[enrichment_column_list[0]])
                            else:
                                # Multiple columns - store as JSON object
                                enrichment_dict = {col: str(row[col]) for col in enrichment_column_list}
                                enrichment_value = json.dumps(enrichment_dict)
                        else:
                            # Column doesn't exist (for col {safe_dataset_name}_exists) - set to True
                            enrichment_value = "true"
                        
                        # Create Dataset record with normalized lead
                        dataset_row = Dataset(
                            project_dataset_id=project_dataset.id,
                            lead=normalized_lead,  # Store normalized version
                            enrichment_value=enrichment_value
                        )
                        session.add(dataset_row)
                        rows_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing row {idx}: {e}")
                        continue
                
                # Update row count
                project_dataset.row_count = rows_processed
                
                # Commit all changes
                session.commit()
                
                logger.info(
                    f"✅ Dataset '{dataset_name}' uploaded: "
                    f"{rows_processed} rows processed"
                )
                
                # Merge dataset leads into merged_results table
                merge_result = None
                try:
                    merge_result = merged_results_service.merge_dataset_leads(
                        project_id=project_id,
                        project_dataset_id=project_dataset.id,
                        enrichment_column_list=enrichment_column_for_merge
                    )
                    logger.info(f"✅ Dataset leads merged: {merge_result.get('message', '')}")
                except Exception as merge_error:
                    # Log merge error but don't fail the upload
                    logger.warning(f"⚠️ Dataset leads merge failed (upload still succeeded): {str(merge_error)}")
                
                # Update project counts (including leads_collected from merged_results) after merge
                project_service.update_project_counts_from_db(project_id)
                
                # Build success message with merge stats
                success_message = f"Dataset '{dataset_name}' uploaded successfully"
                if merge_result:
                    # Include merge stats in the message
                    merge_message = merge_result.get('message', '')
                    if merge_message:
                        success_message += f". {merge_message}"
                
                return {
                    "success": True,
                    "message": success_message,
                    "rows_processed": rows_processed,
                    "project_dataset_id": project_dataset.id
                }
                
        except ValueError as e:
            # Validation errors - don't log as error, just re-raise
            raise
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error uploading dataset: {e}")
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error uploading dataset: {e}")
            raise Exception(f"Error uploading dataset: {str(e)}")

# Global service instance
leads_dataset_service = LeadsDatasetService()

