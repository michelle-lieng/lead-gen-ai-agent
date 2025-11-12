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

