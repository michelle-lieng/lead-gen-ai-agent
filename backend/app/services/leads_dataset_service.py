"""
Dataset upload and management service
"""

import logging
import pandas as pd
import json
from io import BytesIO
from sqlalchemy.exc import SQLAlchemyError

from .database_service import db_service
from .project_service import project_service
from .job_service import job_service
from ..models.tables import ProjectDataset, Dataset, Project
from .merged_results_service import merged_results_service
from ..utils.lead_utils import normalize_lead_name, sanitize_value
from ..exceptions import (
    ProjectNotFoundError,
    DatabaseFailureError,
    InvalidFileError,
    InvalidEnrichmentColumnError,
)

logger = logging.getLogger(__name__)


class LeadsDatasetService:
    """Service for managing dataset uploads and processing"""

    def _merge_excel_sheets(self, excel_content: bytes) -> pd.DataFrame:
        """
        Merge all sheets from an Excel file into a single DataFrame WITHOUT requiring a lead column.
        Column order is based on Sheet 1, and sheets are concatenated vertically (no row merging).

        Logic:
        1. Read Sheet 1 first - this determines the column order
        2. Read all other sheets
        3. For each sheet, add any new columns that don't exist in Sheet 1 (append to end)
        4. Ensure all sheets have all columns (fill missing with blank)
        5. Concatenate all sheets vertically (don't merge rows with same values)

        Args:
            excel_content: Excel file content as bytes

        Returns:
            Merged DataFrame with columns ordered by Sheet 1, all rows concatenated vertically
        """
        excel_file = pd.ExcelFile(BytesIO(excel_content))

        if len(excel_file.sheet_names) == 0:
            return pd.DataFrame()

        # Read Sheet 1 first - this determines column order
        sheet1_name = excel_file.sheet_names[0]
        # Use openpyxl engine to ensure all rows are read
        df_sheet1 = pd.read_excel(
            excel_file, sheet_name=sheet1_name, header=0, engine="openpyxl"
        )
        initial_sheet1_rows = len(df_sheet1)
        df_sheet1.columns = df_sheet1.columns.str.strip()
        df_sheet1 = df_sheet1.dropna(how="all")
        sheet1_rows_after_filter = len(df_sheet1)
        logger.info(
            f"Sheet 1 '{sheet1_name}': Read {initial_sheet1_rows} rows, "
            f"filtered {initial_sheet1_rows - sheet1_rows_after_filter} empty rows, "
            f"{sheet1_rows_after_filter} rows remaining"
        )

        # Sheet 1 columns determine the order (preserve order)
        sheet1_columns = df_sheet1.columns.tolist()
        all_columns_set = set(sheet1_columns)

        # Read all other sheets and collect any new columns
        other_sheets = []
        for sheet_name in excel_file.sheet_names[1:]:
            # Use openpyxl engine to ensure all rows are read
            df_sheet = pd.read_excel(
                excel_file, sheet_name=sheet_name, header=0, engine="openpyxl"
            )
            initial_rows = len(df_sheet)
            df_sheet.columns = df_sheet.columns.str.strip()
            df_sheet = df_sheet.dropna(how="all")
            rows_after_filter = len(df_sheet)
            logger.info(
                f"Sheet '{sheet_name}': Read {initial_rows} rows, "
                f"filtered {initial_rows - rows_after_filter} empty rows, "
                f"{rows_after_filter} rows remaining"
            )
            other_sheets.append((sheet_name, df_sheet))
            all_columns_set.update(df_sheet.columns)

        # Determine final column order: Sheet 1 columns first, then any new columns from other sheets
        new_columns = sorted(
            [col for col in all_columns_set if col not in sheet1_columns]
        )
        final_column_order = sheet1_columns + new_columns

        # Prepare Sheet 1 with all columns
        df_sheet1_final = df_sheet1.copy()
        for col in new_columns:
            if col not in df_sheet1_final.columns:
                df_sheet1_final[col] = ""
        df_sheet1_final = df_sheet1_final[final_column_order]
        df_sheet1_final = df_sheet1_final.fillna("")

        # Prepare other sheets with all columns (in correct order)
        merged_dfs = [df_sheet1_final]

        for sheet_name, df_sheet in other_sheets:
            # Ensure all columns exist in this sheet (fill missing with blank)
            for col in final_column_order:
                if col not in df_sheet.columns:
                    df_sheet[col] = ""

            # Reorder columns to match Sheet 1's order + new columns
            df_sheet = df_sheet[final_column_order]
            df_sheet = df_sheet.fillna("")

            merged_dfs.append(df_sheet)

        # Concatenate all sheets vertically (no row merging)
        merged_df = pd.concat(merged_dfs, ignore_index=True)

        logger.info(
            f"Merged {len(excel_file.sheet_names)} Excel sheet(s): {len(merged_df)} total rows (concatenated vertically)"
        )

        return merged_df

    def upload_dataset(
        self,
        project_id: int,
        dataset_name: str,
        lead_column: str,
        enrichment_column_list: str,  # JSON-encoded string (will be parsed)
        enrichment_column_exists: bool,
        file,  # FastAPI UploadFile object
    ) -> dict:
        """
        Upload and process a CSV or Excel dataset.

        Args:
            project_id: Project ID to link dataset to
            dataset_name: User-friendly name for the dataset
            lead_column: Name of column containing leads (company names)
            enrichment_column_list: JSON-encoded string of enrichment column names
            enrichment_column_exists: Whether the enrichment column exists in file
            file: FastAPI UploadFile object

        Returns:
            dict: Success status and statistics

        Raises:
            JobAlreadyRunningError: If a job is already running
            ProjectNotFoundError: If project does not exist
            InvalidFileError: If file is empty or invalid
            InvalidEnrichmentColumnError: If enrichment column list is invalid
            DatabaseFailureError: If database operation fails
            ValueError: If enrichment column list is invalid
        """
        try:
            # Check if there is a running job
            job_service.check_running_job(project_id, "leads_dataset")

            # Create job
            job = job_service.create_job(project_id, "leads_dataset")

            # Parse JSON-encoded enrichment_column_list string into list
            enrichment_column_list_parsed = []
            if enrichment_column_list and enrichment_column_list.strip():
                try:
                    enrichment_column_list_parsed = json.loads(enrichment_column_list)
                    if not isinstance(enrichment_column_list_parsed, list):
                        job_service.mark_job_as_failed(
                            job.id,
                            f"enrichment_column_list must be a JSON array, got: {type(enrichment_column_list_parsed).__name__}",
                        )
                        raise ValueError(
                            f"enrichment_column_list must be a JSON array, got: {type(enrichment_column_list_parsed).__name__}"
                        )
                except json.JSONDecodeError as e:
                    job_service.mark_job_as_failed(
                        job.id,
                        f"Invalid JSON format for enrichment_column_list. Error: {str(e)}. Received: {repr(enrichment_column_list)}",
                    )
                    raise ValueError(
                        f"Invalid JSON format for enrichment_column_list. Error: {str(e)}. Received: {repr(enrichment_column_list)}"
                    )
            # If enrichment_column_list is empty string or '[]', enrichment_column_list_parsed will be []

            # Read file content
            file_content = file.file.read()

            # Validate filename and determine file type
            if not file.filename:
                job_service.mark_job_as_failed(job.id, "File must have a filename")
                raise InvalidFileError("File must have a filename")

            filename_lower = file.filename.lower()
            is_csv = filename_lower.endswith(".csv")
            is_excel = filename_lower.endswith((".xlsx", ".xls"))

            if not (is_csv or is_excel):
                job_service.mark_job_as_failed(
                    job.id, "File must be a CSV (.csv) or Excel (.xlsx, .xls) file"
                )
                raise InvalidFileError(
                    "File must be a CSV (.csv) or Excel (.xlsx, .xls) file"
                )

            # Validate file is not empty
            if not file_content:
                job_service.mark_job_as_failed(job.id, "File is empty")
                raise InvalidFileError("File is empty")

            with db_service.get_session() as session:
                # Validate project exists
                project = (
                    session.query(Project).filter(Project.id == project_id).first()
                )
                if not project:
                    job_service.mark_job_as_failed(
                        job.id, f"Project with ID {project_id} not found"
                    )
                    raise ProjectNotFoundError(project_id)

                # ============================================================
                # STEP 1: Parse file (CSV or Excel)
                # ============================================================
                if is_excel:
                    # Excel: Merge all sheets by concatenating vertically (no row merging across sheets)
                    # Column order is based on Sheet 1
                    df = self._merge_excel_sheets(file_content)
                    logger.info(
                        f"Merged {len(pd.ExcelFile(BytesIO(file_content)).sheet_names)} Excel sheet(s)"
                    )
                else:
                    # CSV: Read directly
                    df = pd.read_csv(
                        BytesIO(file_content),
                        encoding="utf-8",
                        encoding_errors="replace",
                    )

                # ============================================================
                # STEP 2: Normalize column names and validate
                # ============================================================
                # Strip whitespace from all column names and user inputs
                df.columns = df.columns.str.strip()
                lead_column = lead_column.strip()
                # Strip and filter out empty strings from enrichment column list
                enrichment_column_list_parsed = [
                    col.strip() for col in enrichment_column_list_parsed if col.strip()
                ]

                # Validate lead_column exists in the file
                if lead_column not in df.columns:
                    job_service.mark_job_as_failed(
                        job.id,
                        f"Lead column '{lead_column}' not found in file. Available columns: {', '.join(df.columns)}",
                    )
                    raise ValueError(
                        f"Lead column '{lead_column}' not found in file. Available columns: {', '.join(df.columns)}"
                    )

                # ============================================================
                # STEP 3: Filter out rows with empty/invalid lead_column values
                # ============================================================
                # Remove rows where lead_column is NaN, empty string, 'nan', 'None', or zero-length
                initial_count = len(df)
                df = df[df[lead_column].notna()]
                df[lead_column] = df[lead_column].astype(str).str.strip()
                df = df[
                    (df[lead_column] != "")
                    & (df[lead_column] != "nan")
                    & (df[lead_column] != "None")
                    & (df[lead_column].str.len() > 0)
                ]
                after_empty_filter = len(df)

                # ============================================================
                # STEP 4: Deduplicate leads (case-insensitive)
                # ============================================================
                # Remove duplicate leads, keeping first occurrence
                # Use case-insensitive comparison (e.g., "Apple" and "apple" are duplicates)
                before_dedup = len(df)
                df["_temp_lower_lead"] = (
                    df[lead_column].astype(str).str.strip().str.lower()
                )
                df = df.drop_duplicates(subset=["_temp_lower_lead"], keep="first")
                df = df.drop(columns=["_temp_lower_lead"])
                after_dedup = len(df)

                logger.info(
                    f"File: {initial_count} rows initially, "
                    f"{after_empty_filter} rows after filtering empty lead_column, "
                    f"{after_dedup} rows after deduplication"
                )

                # ============================================================
                # STEP 5: Normalize all leads (vectorized operation for performance)
                # ============================================================
                # Normalize all leads at once using pandas apply (much faster than row-by-row)
                # This removes legal suffixes, normalizes unicode, etc.
                before_normalization = len(df)
                df["_normalized_lead"] = df[lead_column].apply(normalize_lead_name)
                # Filter out rows where normalization resulted in empty string
                # (e.g., "Pty Ltd" becomes "" after removing legal suffixes)
                df = df[df["_normalized_lead"] != ""]
                after_normalization = len(df)
                skipped_normalization = before_normalization - after_normalization

                if skipped_normalization > 0:
                    logger.warning(
                        f"Skipped {skipped_normalization} rows that became empty after normalization"
                    )

                logger.info(
                    f"After normalization: {after_normalization} rows remaining "
                    f"({skipped_normalization} skipped)"
                )

                # ============================================================
                # STEP 6: Handle enrichment columns
                # ============================================================
                if enrichment_column_exists:
                    # User selected enrichment columns from file - verify they all exist
                    if len(enrichment_column_list_parsed) == 0:
                        job_service.mark_job_as_failed(
                            job.id,
                            "enrichment_column_list cannot be empty when enrichment_column_exists is True",
                        )
                        raise InvalidEnrichmentColumnError(
                            "enrichment_column_list cannot be empty when enrichment_column_exists is True"
                        )

                    missing_columns = [
                        col
                        for col in enrichment_column_list_parsed
                        if col not in df.columns
                    ]
                    if missing_columns:
                        job_service.mark_job_as_failed(
                            job.id,
                            f"Enrichment column(s) not found in file: {', '.join(missing_columns)}. Available columns: {', '.join(df.columns)}",
                        )
                        raise InvalidEnrichmentColumnError(
                            f"Enrichment column(s) not found in file: {', '.join(missing_columns)}. "
                            f"Available columns: {', '.join(df.columns)}"
                        )

                    enrichment_column_for_merge = enrichment_column_list_parsed
                    logger.info(
                        f"Using {len(enrichment_column_list_parsed)} enrichment column(s): {', '.join(enrichment_column_list_parsed)}"
                    )
                else:
                    # No enrichment columns in file - create a boolean column (e.g., "dataset_name_exists" = True)
                    safe_dataset_name = sanitize_value(dataset_name)
                    enrichment_column_for_merge = [f"{safe_dataset_name}_exists"]
                    logger.info(
                        f"Creating column '{safe_dataset_name}_exists' with value True"
                    )

                # ============================================================
                # STEP 7: Create ProjectDataset record in database
                # ============================================================
                # This record tracks the dataset metadata (name, columns, row count)
                project_dataset = ProjectDataset(
                    project_id=project_id,
                    dataset_name=dataset_name,
                    lead_column=lead_column,
                    enrichment_column_list=",".join(
                        enrichment_column_for_merge
                    ),  # Store as comma-separated string in DB
                    row_count=0,  # Will update after processing all rows
                )
                session.add(project_dataset)
                session.flush()  # Get the ID without committing yet (need ID for Dataset records)

                # ============================================================
                # STEP 8: Process rows and save to database
                # ============================================================
                # All leads are already normalized and filtered at this point
                rows_processed = 0
                total_rows = len(df)

                logger.info(f"Processing {total_rows} rows from merged DataFrame")

                for idx, row in df.iterrows():
                    try:
                        # Get normalized lead (already computed in STEP 5)
                        normalized_lead = row["_normalized_lead"]

                        # Get enrichment value(s) from the row
                        if (
                            enrichment_column_exists
                            and len(enrichment_column_list_parsed) > 0
                        ):
                            if len(enrichment_column_list_parsed) == 1:
                                # Single enrichment column - store value directly
                                enrichment_value = str(
                                    row[enrichment_column_list_parsed[0]]
                                )
                            else:
                                # Multiple enrichment columns - store as JSON object
                                enrichment_dict = {
                                    col: str(row[col])
                                    for col in enrichment_column_list_parsed
                                }
                                enrichment_value = json.dumps(enrichment_dict)
                        else:
                            # No enrichment columns - set to "true" (boolean flag)
                            enrichment_value = "true"

                        # Create Dataset record with normalized lead
                        dataset_row = Dataset(
                            project_dataset_id=project_dataset.id,
                            lead=normalized_lead,  # Store normalized version for deduplication
                            enrichment_value=enrichment_value,
                        )
                        session.add(dataset_row)
                        rows_processed += 1

                    except Exception as e:
                        logger.exception(f"Error processing row {idx}")
                        continue

                # ============================================================
                # STEP 9: Update metadata and commit
                # ============================================================
                # Update row count in ProjectDataset record
                project_dataset.row_count = rows_processed

                # Commit all changes to database
                session.commit()

                logger.info(
                    f"✅ Dataset '{dataset_name}' uploaded: "
                    f"{rows_processed} rows processed out of {total_rows} total rows"
                )

                # Merge dataset leads into merged_results table
                merge_result = None
                try:
                    merge_result = merged_results_service.merge_dataset_leads(
                        project_id=project_id,
                        project_dataset_id=project_dataset.id,
                        enrichment_column_list=enrichment_column_for_merge,
                    )
                    logger.info(
                        f"✅ Dataset leads merged: {merge_result.get('message', '')}"
                    )
                except Exception as merge_error:
                    # Log merge error but don't fail the upload
                    logger.warning(
                        f"⚠️ Dataset leads merge failed (upload still succeeded): {str(merge_error)}"
                    )

                # Update project counts (including leads_collected from merged_results) after merge
                project_service.update_project_counts_from_db(project_id)

                # Build success message with merge stats
                success_message = f"Dataset '{dataset_name}' uploaded successfully"
                if merge_result:
                    # Include merge stats in the message
                    merge_message = merge_result.get("message", "")
                    if merge_message:
                        success_message += f". {merge_message}"

                # Update job status to completed
                job_service.mark_job_as_completed(job.id)

                return {
                    "success": True,
                    "message": success_message,
                    "rows_processed": rows_processed,
                    "project_dataset_id": project_dataset.id,
                }

        except SQLAlchemyError as e:
            logger.exception("❌ Database error uploading dataset")
            job_service.mark_job_as_failed(job.id, str(e))
            raise DatabaseFailureError("Failed to upload dataset") from e


# Global service instance
leads_dataset_service = LeadsDatasetService()
