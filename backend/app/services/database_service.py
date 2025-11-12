"""
Database service using SQLAlchemy
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

import logging
from io import StringIO
import csv
from flask import Response
from datetime import datetime
from pathlib import Path

from ..config import settings
from ..models.tables import Base

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        """Initialize database service with connection to the main database"""
        self.connection_string = (
            f"postgresql://{settings.postgresql_user}:{settings.postgresql_password}"
            f"@{settings.postgresql_host}:{settings.postgresql_port}/{settings.postgresql_database}"
        )
        # This creates the connection pool (default to 5 connections in the pool)
        # Think of it like parking spaces how many sessions we can create
        self.engine = create_engine(self.connection_string)
        # this is the factory for creating new sessions
        # this attachs the get_sessions with the connection pool
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_session(self) -> Session:
        """Get database session - this creates new session
        (using our factory in the init and connecting to our connection pool)
        
        Note to self: When we make changes in session they are not saved yet
        only stagged. It is only when we go session.commit() that the changes
        are saved. We can do session.rollback() to cancel staged changes.
        Session.close() then ends the conversation. 
        
        We don't actually use it in the code below because we use the with self.getsession() 
        which will automatically close it after the code runs. We need to close our sessions 
        otherwise they take up RAM.

        # 5 connections in the pool (by engine)
        # 🅿️ [Conn1] [Conn2] [Conn3] [Conn4] [Conn5]

        # Create 5 sessions (all get connections)
        session1 = SessionLocal()  # Gets Conn1
        session2 = SessionLocal()  # Gets Conn2
        session3 = SessionLocal()  # Gets Conn3
        session4 = SessionLocal()  # Gets Conn4
        session5 = SessionLocal()  # Gets Conn5

        # 🅿️ [Conn1 in use] [Conn2 in use] [Conn3 in use] [Conn4 in use] [Conn5 in use]

        # Try to create 6th session
        session6 = SessionLocal()  # Waits! No connections available
        """
        return self.SessionLocal()
    
    def check_database_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def check_table_exists(self, table_name: str = "projects") -> bool:
        """Check if a table exists"""
        try:
            logger.info(f"🔍 Checking if table '{table_name}' exists...")
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    );
                """), {"table_name": table_name}).scalar()
                logger.info(f"🔍 Table '{table_name}' exists: {result}")
                return result
        except Exception as e:
            logger.error(f"❌ Error checking table existence: {e}")
            return False
    
    def check_all_tables_exist(self) -> bool:
        """Check if all required tables exist"""
        required_tables = [
            "projects",
            "serp_queries",
            "serp_urls",
            "serp_leads",
            "serp_leads_aggregated",
            "project_datasets",
            "datasets",
            "merged_results"
        ]
        for table_name in required_tables:
            if not self.check_table_exists(table_name):
                logger.info(f"❌ Table '{table_name}' does not exist")
                return False
        logger.info("✅ All required tables exist")
        return True
    
    def create_tables(self) -> bool:
        """Create all tables ONLY if they don't exist"""
        try:
            # Test database connection first
            if not self.check_database_connection():
                raise Exception("Database connection failed")
            
            # Check if all tables already exist - if yes, skip creation
            if self.check_all_tables_exist():
                logger.info("✅ All required tables already exist - skipping creation")
                return True
            
            # Only create tables if they don't exist
            logger.info("📝 Some tables don't exist - creating all tables now...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
            
            # Verify all tables were actually created
            if self.check_all_tables_exist():
                logger.info("✅ All table creation verified")
                return True
            else:
                logger.error("❌ Table creation failed - some tables not found after creation")
                raise Exception("Table creation failed - some tables not found after creation")
                
        except SQLAlchemyError as e:
            logger.error(f"❌ SQLAlchemy error creating tables: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

    def export_table_as_csv(self, table_name: str | list[str]):
        """
        Export any table to CSV file
        
        Args:
            table_name (str | list): Name of the table(s) to export
        
        Returns:
            str | list[str]: Path(s) to the created CSV file(s)
        """
        try:
            csv_paths = []
            # Convert single table name to list for uniform processing
            if isinstance(table_name, str):
                tables = [table_name]
            else:
                tables = table_name
            
            for table in tables:
                # Check if table exists
                if not self.check_table_exists(table):
                    raise Exception(f"Table '{table}' does not exist")
                
                # Create standard output directory
                output_dir = Path.cwd() / "output" / table
                filename_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                outdir = output_dir / filename_ts
                outdir.mkdir(parents=True, exist_ok=True)
                
                # Build the query - special case for serp_urls table
                if table == "serp_urls":
                    query = "SELECT id, project_id, query, title, link, snippet, LEFT(website_scraped, 32600) AS website_scraped, status, created_at FROM serp_urls"
                else:
                    query = f"SELECT * FROM {table}"
                
                # Export to CSV
                csv_filename = f"{table}.csv"
                csv_path = outdir / csv_filename
                
                with self.get_session() as session:
                    # Execute query and get results
                    result = session.execute(text(query))
                    rows = result.fetchall()
                    
                    if not rows:
                        logger.warning(f"⚠️ Table '{table}' is empty")
                        csv_paths.append(str(csv_path))
                        continue
                    
                    # Get column names from the first row
                    columns = list(result.keys())
                    
                    # Write to CSV
                    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        # Write header
                        writer.writerow(columns)
                        # Write data rows
                        writer.writerows(rows)
                
                logger.info(f"✅ Table '{table}' exported to {csv_path}")
                csv_paths.append(str(csv_path))
            
            # Return single path if single table, list if multiple tables
            if isinstance(table_name, str):
                return csv_paths[0] if csv_paths else None
            return csv_paths
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error exporting table(s): {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error exporting table(s): {e}")
            raise
    
# Global database service instance
db_service = DatabaseService()

# Testing section
if __name__ == "__main__":
    """
    Quick testing of database service functions
    Run with: python -m app.services.database_service
    """
    import sys
    import os

    db_service.export_table_as_csv(["serp_urls", "serp_leads"])
    
    # Add the backend directory to Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    print("🧪 Testing Database Service...")
    
    try:
        # Test 1: Check database connection
        print("\n1️⃣ Testing database connection...")
        connected = db_service.check_database_connection()
        print(f"✅ Database connected: {connected}")
        
        # Test 2: Check table exists
        print("\n2️⃣ Testing table existence...")
        table_exists = db_service.check_table_exists()
        print(f"✅ Table exists: {table_exists}")
        
        # Test 3: Create tables (if needed)
        print("\n3️⃣ Testing table creation...")
        created = db_service.create_tables()
        print(f"✅ Tables created: {created}")
        
        print("\n🎉 Database service tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()