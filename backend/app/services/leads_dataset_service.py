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

    def _merge_excel_sheets_preview(self, excel_content: bytes) -> pd.DataFrame:
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
        df_sheet1 = pd.read_excel(excel_file, sheet_name=sheet1_name, header=0, engine='openpyxl')
        initial_sheet1_rows = len(df_sheet1)
        df_sheet1.columns = df_sheet1.columns.str.strip()
        df_sheet1 = df_sheet1.dropna(how='all')
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
            df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name, header=0, engine='openpyxl')
            initial_rows = len(df_sheet)
            df_sheet.columns = df_sheet.columns.str.strip()
            df_sheet = df_sheet.dropna(how='all')
            rows_after_filter = len(df_sheet)
            logger.info(
                f"Sheet '{sheet_name}': Read {initial_rows} rows, "
                f"filtered {initial_rows - rows_after_filter} empty rows, "
                f"{rows_after_filter} rows remaining"
            )
            other_sheets.append((sheet_name, df_sheet))
            all_columns_set.update(df_sheet.columns)
        
        # Determine final column order: Sheet 1 columns first, then any new columns from other sheets
        new_columns = sorted([col for col in all_columns_set if col not in sheet1_columns])
        final_column_order = sheet1_columns + new_columns
        
        # Prepare Sheet 1 with all columns
        df_sheet1_final = df_sheet1.copy()
        for col in new_columns:
            if col not in df_sheet1_final.columns:
                df_sheet1_final[col] = ''
        df_sheet1_final = df_sheet1_final[final_column_order]
        df_sheet1_final = df_sheet1_final.fillna('')
        
        # Prepare other sheets with all columns (in correct order)
        merged_dfs = [df_sheet1_final]
        
        for sheet_name, df_sheet in other_sheets:
            # Ensure all columns exist in this sheet (fill missing with blank)
            for col in final_column_order:
                if col not in df_sheet.columns:
                    df_sheet[col] = ''
            
            # Reorder columns to match Sheet 1's order + new columns
            df_sheet = df_sheet[final_column_order]
            df_sheet = df_sheet.fillna('')
            
            merged_dfs.append(df_sheet)
        
        # Concatenate all sheets vertically (no row merging)
        merged_df = pd.concat(merged_dfs, ignore_index=True)
        
        logger.info(f"Merged {len(excel_file.sheet_names)} Excel sheet(s): {len(merged_df)} total rows (concatenated vertically)")
        
        return merged_df

    def _merge_excel_sheets(self, excel_content: bytes, lead_column: str) -> pd.DataFrame:
        """
        Merge all sheets from an Excel file into a single DataFrame.
        
        Logic:
        1. Read all sheets from the Excel file
        2. Collect all unique columns across all sheets
        3. Merge sheets on lead_column (outer join)
        4. Fill missing columns with blank values
        5. If same lead_column value exists in multiple sheets, combine into one row
        6. Handle duplicate columns by preferring non-null values
        
        Args:
            excel_content: Excel file content as bytes
            lead_column: Name of the column to use as primary identifier for merging
            
        Returns:
            Merged DataFrame with all columns from all sheets
        """
        excel_file = pd.ExcelFile(BytesIO(excel_content))
        
        all_sheets = []
        all_columns = set()
        
        # First pass: read all sheets and collect all column names
        for sheet_name in excel_file.sheet_names:
            df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
            # Normalize column names (strip whitespace)
            df_sheet.columns = df_sheet.columns.str.strip()
            # Drop completely empty rows (all values are NaN)
            df_sheet = df_sheet.dropna(how='all')
            logger.info(f"Sheet '{sheet_name}': Read {len(df_sheet)} rows from Excel file")
            all_sheets.append((sheet_name, df_sheet))
            all_columns.update(df_sheet.columns)
        
        # Ensure lead_column exists in at least one sheet
        if lead_column not in all_columns:
            raise ValueError(
                f"Lead column '{lead_column}' not found in any sheet. "
                f"Available columns: {', '.join(sorted(all_columns))}"
            )
        
        # Merge all sheets on lead_column
        merged_df = None
        
        for sheet_name, df_sheet in all_sheets:
            # Ensure lead_column exists in this sheet, if not add it with NaN values
            if lead_column not in df_sheet.columns:
                df_sheet[lead_column] = None
            
            # Filter out rows where lead_column is NaN BEFORE converting to string
            # This prevents NaN from becoming the string 'nan'
            initial_row_count = len(df_sheet)
            df_sheet = df_sheet[df_sheet[lead_column].notna()]
            
            # Now convert to string and strip whitespace
            df_sheet[lead_column] = df_sheet[lead_column].astype(str).str.strip()
            
            # Remove rows where lead_column is empty or invalid strings
            df_sheet = df_sheet[
                (df_sheet[lead_column] != '') & 
                (df_sheet[lead_column] != 'nan') &
                (df_sheet[lead_column] != 'None') &
                (df_sheet[lead_column].str.len() > 0)
            ]
            
            filtered_count = initial_row_count - len(df_sheet)
            logger.info(f"Sheet '{sheet_name}': Started with {initial_row_count} rows, filtered out {filtered_count} empty/invalid rows, {len(df_sheet)} rows remaining")
            
            if merged_df is None:
                # First sheet - use it as base
                merged_df = df_sheet.copy()
            else:
                # Merge with existing data
                # Use outer join to keep all rows from both sheets
                # If same lead_column value exists in both, combine the rows (fill missing columns with blank)
                merged_df = pd.merge(
                    merged_df,
                    df_sheet,
                    on=lead_column,
                    how='outer',
                    suffixes=('', '_new')
                )
                
                # Handle duplicate columns (columns that exist in both sheets)
                # For duplicate columns (except lead_column), prefer non-null values
                for col in df_sheet.columns:
                    if col != lead_column and col in merged_df.columns:
                        # Check if we have a _new suffix version
                        new_col = f"{col}_new"
                        if new_col in merged_df.columns:
                            # Prefer non-null values, fill missing with blank
                            merged_df[col] = merged_df[col].fillna(merged_df[new_col]).fillna('')
                            merged_df = merged_df.drop(columns=[new_col])
                        else:
                            # Column exists but no new version - fill missing with blank
                            merged_df[col] = merged_df[col].fillna('')
                
                # Add any new columns that don't exist in merged_df yet
                for col in df_sheet.columns:
                    if col not in merged_df.columns:
                        merged_df[col] = ''
        
        # Ensure all columns from all sheets are present (fill missing with blank)
        for col in all_columns:
            if col not in merged_df.columns:
                merged_df[col] = ''
        
                # Fill all NaN values with empty string
                merged_df = merged_df.fillna('')
                
                # Remove duplicate rows based on lead_column (keep first occurrence)
                # But only if lead_column is not empty
                before_dedup = len(merged_df)
                merged_df = merged_df[merged_df[lead_column].notna() & (merged_df[lead_column] != '') & (merged_df[lead_column] != 'nan')]
                merged_df = merged_df.drop_duplicates(subset=[lead_column], keep='first')
                after_dedup = len(merged_df)
                
                # Sort by lead_column for consistency
                merged_df = merged_df.sort_values(by=lead_column).reset_index(drop=True)
                
                logger.info(f"Merged Excel sheets: {before_dedup} rows before deduplication, {after_dedup} rows after deduplication")
                
                return merged_df

    def upload_dataset(
        self,
        project_id: int,
        dataset_name: str,
        lead_column: str,
        enrichment_column_list: list[str],  # Always a list (empty if no enrichment columns)
        enrichment_column_exists: bool,
        file_content: bytes,  # CSV or Excel file as bytes
        is_excel: bool = False  # Whether the file is Excel format
    ) -> dict:
        """
        Upload and process a CSV or Excel dataset.
        
        Args:
            project_id: Project ID to link dataset to
            dataset_name: User-friendly name for the dataset
            lead_column: Name of column containing leads (company names)
            enrichment_column_list: Name of column(s) for enrichment values in list
            enrichment_column_exists: Whether the enrichment column exists in file
            file_content: CSV or Excel file content as bytes
            is_excel: Whether the file is Excel format (.xlsx, .xls)
            
        Returns:
            dict: Success status and statistics
        """
        try:
            with db_service.get_session() as session:
                # Validate project exists
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project {project_id} not found")
                
                # Parse file based on type
                try:
                    if is_excel:
                        # Merge all sheets by concatenating vertically (no row merging across sheets)
                        # Column order is based on Sheet 1
                        df = self._merge_excel_sheets_preview(file_content)
                        
                        # Validate lead_column exists
                        if lead_column not in df.columns:
                            raise ValueError(
                                f"Lead column '{lead_column}' not found. "
                                f"Available columns: {', '.join(df.columns.tolist())}"
                            )
                        
                        # Filter out rows where lead_column is empty
                        initial_count = len(df)
                        df = df[df[lead_column].notna()]
                        df[lead_column] = df[lead_column].astype(str).str.strip()
                        df = df[
                            (df[lead_column] != '') & 
                            (df[lead_column] != 'nan') &
                            (df[lead_column] != 'None') &
                            (df[lead_column].str.len() > 0)
                        ]
                        
                        # Deduplicate based on lead_column (keep first occurrence)
                        # This removes duplicates within the concatenated data
                        before_dedup = len(df)
                        df = df.drop_duplicates(subset=[lead_column], keep='first')
                        after_dedup = len(df)
                        
                        logger.info(
                            f"Merged {len(pd.ExcelFile(BytesIO(file_content)).sheet_names)} Excel sheet(s): "
                            f"{initial_count} rows before filtering, {before_dedup} rows after filtering empty lead_column, "
                            f"{after_dedup} rows after deduplication"
                        )
                    else:
                        # Parse CSV
                        df = pd.read_csv(BytesIO(file_content), encoding='utf-8', encoding_errors='replace')
                except ValueError as e:
                    # Re-raise ValueError (e.g., lead column not found)
                    raise
                except Exception as e:
                    file_type = "Excel" if is_excel else "CSV"
                    raise ValueError(f"Failed to parse {file_type} file: {str(e)}")
                
                # Normalize column names (strip whitespace)
                df.columns = df.columns.str.strip()
                lead_column = lead_column.strip()
                enrichment_column_list = [col.strip() for col in enrichment_column_list]
                
                # Normalize column names (strip whitespace)
                df.columns = df.columns.str.strip()
                lead_column = lead_column.strip()
                enrichment_column_list = [col.strip() for col in enrichment_column_list]
                
                # Validate lead_column exists
                file_type = "Excel" if is_excel else "CSV"
                if lead_column not in df.columns:
                    raise ValueError(f"Lead column '{lead_column}' not found in {file_type} file. Available columns: {', '.join(df.columns)}")
                
                # Handle enrichment columns (can be single or multiple)
                if enrichment_column_exists:
                    # User selected columns from CSV - verify they all exist
                    if len(enrichment_column_list) == 0:
                        raise ValueError("enrichment_column_list cannot be empty when enrichment_column_exists is True")
                    
                    missing_columns = [col for col in enrichment_column_list if col not in df.columns]
                    if missing_columns:
                        file_type = "Excel" if is_excel else "CSV"
                        raise ValueError(
                            f"Enrichment column(s) not found in {file_type} file: {', '.join(missing_columns)}. "
                            f"Available columns: {', '.join(df.columns)}"
                        )
    
                    enrichment_column_for_merge = enrichment_column_list
                    file_type = "Excel" if is_excel else "CSV"
                    logger.info(f"Using {len(enrichment_column_list)} enrichment column(s) from {file_type}: {', '.join(enrichment_column_list)}")
                else:
                    # Single enrichment column - will be created with value True
                    safe_dataset_name = sanitize_value(dataset_name)
                    enrichment_column_for_merge = [f"{safe_dataset_name}_exists"]
                    logger.info(f"Creating column '{safe_dataset_name}_exists' with value True")
                
                # Check for duplicate leads (case-insensitive, whitespace-trimmed)
                # Note: After Excel sheet merging, duplicates should already be handled,
                # but we check again to ensure data integrity
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
                    
                    file_type = "Excel" if is_excel else "CSV"
                    raise ValueError(
                        f"Duplicate leads found in {file_type} file. Each lead must be unique. "
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
                skipped_empty = 0
                skipped_normalization = 0
                total_rows = len(df)
                
                logger.info(f"Processing {total_rows} rows from merged DataFrame")
                
                for idx, row in df.iterrows():
                    try:
                        # Get lead value - handle NaN properly
                        if pd.isna(row[lead_column]):
                            skipped_empty += 1
                            if skipped_empty <= 5:  # Log first 5 skipped rows
                                logger.warning(f"Skipping row {idx}: lead column is NaN")
                            continue
                        
                        lead_value = str(row[lead_column]).strip()
                        if not lead_value or lead_value.lower() in ['nan', 'none', '']:
                            skipped_empty += 1
                            if skipped_empty <= 5:  # Log first 5 skipped rows
                                logger.warning(f"Skipping row {idx}: empty lead value: '{lead_value}'")
                            continue
                        
                        # Normalize lead name before saving (lowercase, trim whitespace)
                        normalized_lead = normalize_lead_name(lead_value)
                        
                        # Skip empty leads after normalization
                        if not normalized_lead:
                            skipped_normalization += 1
                            if skipped_normalization <= 5:  # Log first 5 skipped rows
                                logger.warning(f"Skipping row {idx}: lead '{lead_value}' became empty after normalization")
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
                    f"{rows_processed} rows processed out of {total_rows} total rows "
                    f"({skipped_empty} skipped empty, {skipped_normalization} skipped after normalization)"
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

