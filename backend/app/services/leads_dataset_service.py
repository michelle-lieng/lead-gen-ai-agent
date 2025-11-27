"""
Dataset upload and management service
"""
import logging
import pandas as pd
import csv
import re
from io import BytesIO, StringIO
from datetime import datetime
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from .database_service import db_service
from .project_service import project_service
from ..models.tables import ProjectDataset, Dataset, Project
from .merged_results_service import merged_results_service
from ..utils.lead_utils import normalize_lead_name

logger = logging.getLogger(__name__)


class LeadsDatasetService:
    """Service for managing dataset uploads and processing"""

    def upload_dataset(
        self,
        project_id: int,
        dataset_name: str,
        lead_column: str,
        enrichment_column: str,
        enrichment_column_exists: bool,
        csv_content: bytes  # CSV file as bytes
    ) -> dict:
        """
        Upload and process a CSV dataset.
        
        Args:
            project_id: Project ID to link dataset to
            dataset_name: User-friendly name for the dataset
            lead_column: Name of column containing leads (company names)
            enrichment_column: Name of column for enrichment values
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
                try:
                    # Try reading as bytes first (if uploaded file)
                    df = pd.read_csv(BytesIO(csv_content))
                except:
                    # Fallback to string if already decoded
                    df = pd.read_csv(StringIO(csv_content.decode('utf-8')))
                
                # Normalize column names (strip whitespace, handle case)
                df.columns = df.columns.str.strip()
                lead_column = lead_column.strip()
                enrichment_column = enrichment_column.strip()
                
                # Validate lead_column exists
                if lead_column not in df.columns:
                    raise ValueError(f"Lead column '{lead_column}' not found in CSV. Available columns: {', '.join(df.columns)}")
                
                # Handle enrichment column
                enrichment_exists_in_csv = enrichment_column in df.columns
                
                if enrichment_column_exists:
                    # User says column exists - verify it does
                    if not enrichment_exists_in_csv:
                        raise ValueError(
                            f"Enrichment column '{enrichment_column}' not found in CSV, "
                            f"but you indicated it exists. Available columns: {', '.join(df.columns)}"
                        )                    
                else:
                    logger.info(f"Creating column '{enrichment_column}' with value True")
                
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
                    enrichment_column=enrichment_column,
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
                        
                        # Get enrichment value
                        if enrichment_column_exists and enrichment_exists_in_csv:
                            # Use actual value from CSV
                            enrichment_value = row[enrichment_column]
                        else:
                            # Column doesn't exist - set to True
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
                
                # Update project dataset count
                project_service.update_project_counts_from_db(project_id)
                
                logger.info(
                    f"✅ Dataset '{dataset_name}' uploaded: "
                    f"{rows_processed} rows processed"
                )
                
                # Merge dataset leads into merged_results table
                try:
                    merge_result = merged_results_service.merge_dataset_leads(
                        project_id=project_id,
                        project_dataset_id=project_dataset.id,
                        enrichment_column=enrichment_column
                    )
                    logger.info(f"✅ Dataset leads merged: {merge_result.get('message', '')}")
                except Exception as merge_error:
                    # Log merge error but don't fail the upload
                    logger.warning(f"⚠️ Dataset leads merge failed (upload still succeeded): {str(merge_error)}")
                
                return {
                    "success": True,
                    "message": f"Dataset '{dataset_name}' uploaded successfully",
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

