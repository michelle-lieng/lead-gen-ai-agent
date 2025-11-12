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

from .database_service import db_service
from .project_service import project_service
from ..models.tables import SerpLeadAggregated, Dataset, ProjectDataset, MergedResult
from ..utils.lead_utils import normalize_lead_name

logger = logging.getLogger(__name__)


class MergedResultsService:
    """Service for merging SERP leads and dataset leads into merged_results table"""

    def _ensure_enrichment_column_exists(self, column_name: str) -> bool:
        """
        Ensure an enrichment column exists in merged_results table.
        Adds the column if it doesn't exist.
        
        Args:
            column_name: Name of the enrichment column to ensure exists
            
        Returns:
            bool: True if column exists or was created successfully
        """
        try:
            # Sanitize column name to prevent SQL injection
            # Only allow alphanumeric and underscores
            safe_column_name = re.sub(r'[^a-zA-Z0-9_]', '', column_name)
            if not safe_column_name or safe_column_name != column_name:
                logger.error(f"Invalid column name: {column_name}")
                return False
            
            with db_service.get_session() as session:
                # Check if column exists
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'merged_results' 
                    AND column_name = :column_name
                """)
                result = session.execute(check_query, {"column_name": safe_column_name}).fetchone()
                
                if result:
                    # Column already exists
                    return True
                
                # Add column if it doesn't exist
                alter_query = text(f"""
                    ALTER TABLE merged_results 
                    ADD COLUMN {safe_column_name} TEXT
                """)
                session.execute(alter_query)
                session.commit()
                
                logger.info(f"✅ Added enrichment column '{safe_column_name}' to merged_results table")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error ensuring enrichment column '{column_name}' exists: {str(e)}")
            return False

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
                
        except Exception as e:
            logger.error(f"❌ Error merging SERP leads: {str(e)}")
            raise Exception(f"Error merging SERP leads: {str(e)}")

