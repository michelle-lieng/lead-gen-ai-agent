"""
Dataset upload and management service
"""
import logging
import pandas as pd
import csv
import zipfile
import re
from io import BytesIO, StringIO
from datetime import datetime
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from .database_service import db_service
from .project_service import project_service
from ..models.tables import ProjectDataset, Dataset, Project

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
                        # Get lead value
                        lead_value = str(row[lead_column]).strip()
                        if not lead_value or pd.isna(row[lead_column]):
                            logger.warning(f"Skipping row {idx}: empty lead value")
                            continue
                        
                        # Get enrichment value
                        if enrichment_column_exists and enrichment_exists_in_csv:
                            # Use actual value from CSV
                            enrichment_value = row[enrichment_column]
                        else:
                            # Column doesn't exist - set to True
                            enrichment_value = "true"
                        
                        # Create Dataset record
                        dataset_row = Dataset(
                            project_dataset_id=project_dataset.id,
                            lead=lead_value,
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

    def _export_all_data_as_csv(self, project_id: int) -> dict:
        """
        Export ALL dataset data as CSV(s) for project_datasets and datasets tables for the project.
        
        Args:
            project_id: Project ID
            
        Returns:
            dict: Contains CSV content as strings for project_datasets and datasets
        """
        try:
            with db_service.get_session() as session:
                csv_files = {}
                
                # Get all project_datasets for this project
                project_datasets = session.query(ProjectDataset).filter(
                    ProjectDataset.project_id == project_id
                ).all()
                
                if project_datasets:
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["id", "project_id", "dataset_name", "lead_column", "enrichment_column", "row_count", "created_at"])
                    for record in project_datasets:
                        writer.writerow([
                            record.id,
                            record.project_id,
                            record.dataset_name,
                            record.lead_column,
                            record.enrichment_column,
                            record.row_count,
                            record.created_at.isoformat()
                        ])
                    csv_files["project_datasets"] = output.getvalue()
                
                # Get all datasets for this project (through project_datasets)
                if project_datasets:
                    # Get all dataset rows for all project_datasets in this project
                    project_dataset_ids = [pd.id for pd in project_datasets]
                    datasets = session.query(Dataset).filter(
                        Dataset.project_dataset_id.in_(project_dataset_ids)
                    ).all()
                    
                    if datasets:
                        output = StringIO()
                        writer = csv.writer(output)
                        writer.writerow(["id", "project_dataset_id", "lead", "enrichment_value", "created_at"])
                        for record in datasets:
                            writer.writerow([
                                record.id,
                                record.project_dataset_id,
                                record.lead,
                                record.enrichment_value,
                                record.created_at.isoformat()
                            ])
                        csv_files["datasets"] = output.getvalue()
            
            return {"csv_files": csv_files}
                
        except Exception as e:
            logger.error(f"❌ Error exporting dataset data as CSV: {str(e)}")
            raise

    def export_all_data_as_zip(self, project_id: int) -> tuple[bytes, str]:
        """
        Export all dataset data as a ZIP file containing CSV files.
        
        This is the main export method that should be used by API routes.
        It generates a ZIP file with all dataset data (project_datasets, datasets) as CSV files.
        
        Args:
            project_id: Project ID
            
        Returns:
            tuple[bytes, str]: 
                - zip_file_bytes: Binary content of the ZIP file
                - filename: Suggested filename for download (e.g., "project_name_datasets_20240101_120000.zip")
            
        Raises:
            ValueError: If no data found for project or project doesn't exist
        """
        try:
            # Step 1: Get CSV data using private method
            export_result = self._export_all_data_as_csv(project_id)
            csv_files = export_result.get("csv_files", {})
            
            # Step 2: Validate that we have data
            if not csv_files:
                raise ValueError("No dataset data found for this project")
            
            # Step 3: Generate timestamp for filename
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Step 4: Get project name for meaningful filename
            project = project_service.get_project(project_id)
            project_name = project.project_name
            
            # Step 5: Sanitize project name for filename
            # Remove special characters, keep alphanumeric, spaces, hyphens, underscores
            safe_project_name = re.sub(r'[^\w\s-]', '', project_name).strip().replace(' ', '_')
            
            # Step 6: Generate ZIP filename
            zip_filename = f"{safe_project_name}_datasets_{timestamp_str}.zip"
            
            # Step 7: Create ZIP file in memory
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for name, csv_content in csv_files.items():
                    # Encode CSV with UTF-8 BOM for Excel compatibility
                    zip_file.writestr(f"dataset_{name}.csv", csv_content.encode('utf-8-sig'))
            
            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()
            
            logger.info(f"✅ Generated dataset ZIP file for project {project_id}: {zip_filename} ({len(zip_bytes)} bytes)")
            
            return zip_bytes, zip_filename
                
        except ValueError:
            # Re-raise ValueError as-is (for "no data" or "project not found")
            raise
        except Exception as e:
            logger.error(f"❌ Error exporting dataset data as ZIP: {str(e)}")
            raise

# Global service instance
leads_dataset_service = LeadsDatasetService()

