"""
Project service for managing project operations
"""
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from typing import List, Optional
import logging

from ..models.tables import Project, SerpUrl, SerpLead, SerpQuery, ProjectDataset, MergedResult
from .database_service import db_service

logger = logging.getLogger(__name__)

class ProjectService:
    """Service for project-related database operations"""

    def create_project(self, 
        project_name: str,
        description: Optional[str] = None) -> Project:
        """Create a new project"""
        try:
            # this line returns a SQL Alchemy Session object --> have the query(), filter(), first() methods
            with db_service.get_session() as session:
                # Check if project name already exists
                existing_project = session.query(Project).filter(Project.project_name == project_name).first()
                if existing_project:
                    raise ValueError(f"Project name '{project_name}' already exists")
                
                project = Project(
                    project_name=project_name,
                    description=description)
                session.add(project)
                session.commit() #save data to database
                session.refresh(project) # updates python object with database values to return 
                logger.info(f"✅ Created project: {project_name}")
                return project
        except ValueError:
            # Re-raise ValueError for duplicate project names
            raise
        except SQLAlchemyError as e:
            logger.error(f"❌ Error creating project: {e}")
            raise
    
    def get_projects(self) -> List[Project]:
        """Get all projects, refreshing counts from database before returning"""
        try:
            # Refresh all project counts first to ensure accuracy
            self.update_project_counts_from_db()  # None = all projects
            
            with db_service.get_session() as session:
                return session.query(Project).order_by(Project.date_added.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting projects: {e}")
            raise
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get specific project by ID, refreshing counts from database before returning"""
        try:
            # Refresh project counts first to ensure accuracy
            self.update_project_counts_from_db(project_id)
            
            with db_service.get_session() as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project with ID {project_id} does not exist. Please create the project first.")
                return project
        except ValueError:
            # Re-raise ValueError (project not found)
            raise
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting project {project_id}: {e}")
            raise
    
    def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        """Update project fields"""
        try:
            with db_service.get_session() as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    logger.warning(f"Project {project_id} not found")
                    return None
                
                # Prevent removing lead_minimum_criteria - it's required
                if 'lead_minimum_criteria' in kwargs:
                    new_criteria = kwargs['lead_minimum_criteria']
                    if new_criteria is None or (isinstance(new_criteria, str) and not new_criteria.strip()):
                        raise ValueError("lead_minimum_criteria cannot be removed or set to empty. It is required for lead extraction.")
                
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                
                session.commit()
                session.refresh(project)
                logger.info(f"✅ Updated project {project_id}")
                return project
        except ValueError:
            # Re-raise ValueError for validation errors
            raise
        except SQLAlchemyError as e:
            logger.error(f"❌ Error updating project {project_id}: {e}")
            raise
    
    def delete_project(self, project_id: int) -> bool:
        """Delete project by ID, including all related records (cascade deletes automatically)"""
        try:
            with db_service.get_session() as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    logger.warning(f"Project {project_id} not found")
                    return False
                
                # Count related records for logging (before deletion)
                leads_count = session.query(SerpLead).filter(SerpLead.project_id == project_id).count()
                urls_count = session.query(SerpUrl).filter(SerpUrl.project_id == project_id).count()
                queries_count = session.query(SerpQuery).filter(SerpQuery.project_id == project_id).count()
                datasets_count = session.query(ProjectDataset).filter(ProjectDataset.project_id == project_id).count()
                
                # Delete the project - cascade will automatically delete all related records
                # (serp_queries, serp_urls, serp_leads, project_datasets and their dataset rows)
                session.delete(project)
                session.commit()
                
                logger.info(f"✅ Deleted project {project_id} and {leads_count} leads, {urls_count} URLs, {queries_count} queries, {datasets_count} datasets (cascade delete)")
                return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Error deleting project {project_id}: {e}")
            raise
    
    def update_project_counts_from_db(self, project_id: Optional[int] = None) -> bool:
        """
        Recalculate and update project counts from database tables.
        Counts only URLs with status='processed' or 'skip' from serp_urls, total unique leads from merged_results,
        and all datasets from project_datasets.
        
        Args:
            project_id (int, optional): ID of the project to update. If None, updates all projects.
            
        Returns:
            bool: True if successful, False if project not found (when project_id is provided)
        """
        try:            
            with db_service.get_session() as session:
                if project_id is not None:
                    # Update specific project
                    project = session.query(Project).filter(Project.id == project_id).first()
                    if not project:
                        logger.warning(f"Project {project_id} not found for count update")
                        return False
                    
                    # Count only processed or skipped URLs for this project
                    urls_count = session.query(SerpUrl).filter(
                        SerpUrl.project_id == project_id,
                        or_(SerpUrl.status == "processed", SerpUrl.status == "skip")
                    ).count()
                    
                    # Count leads from merged_results table (total unique leads)
                    leads_count = session.query(MergedResult).filter(
                        MergedResult.project_id == project_id
                    ).count()
                    
                    # Count datasets for this project
                    datasets_count = session.query(ProjectDataset).filter(
                        ProjectDataset.project_id == project_id
                    ).count()
                    
                    # Update project counts
                    project.urls_processed = urls_count
                    project.leads_collected = leads_count
                    project.datasets_added = datasets_count
                    
                    session.commit()
                    logger.info(f"✅ Updated counts for project {project_id}: {urls_count} processed URLs, {leads_count} leads, {datasets_count} datasets")
                    return True
                else:
                    # Update all projects
                    projects = session.query(Project).all()
                    updated_count = 0
                    
                    for project in projects:
                        # Count processed or skipped URLs for this project
                        urls_count = session.query(SerpUrl).filter(
                            SerpUrl.project_id == project.id,
                            or_(SerpUrl.status == "processed", SerpUrl.status == "skip")
                        ).count()
                        
                        # Count leads from merged_results table (total unique leads)
                        leads_count = session.query(MergedResult).filter(
                            MergedResult.project_id == project.id
                        ).count()
                        
                        # Count datasets for this project
                        datasets_count = session.query(ProjectDataset).filter(
                            ProjectDataset.project_id == project.id
                        ).count()
                        
                        # Update project counts
                        project.urls_processed = urls_count
                        project.leads_collected = leads_count
                        project.datasets_added = datasets_count
                        updated_count += 1
                    
                    session.commit()
                    logger.info(f"✅ Updated counts for {updated_count} project(s)")
                    return True
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error updating project counts for {project_id if project_id else 'all projects'}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error updating project counts for {project_id if project_id else 'all projects'}: {e}")
            return False

# Global project service instance
project_service = ProjectService()

# Testing section
if __name__ == "__main__":
    """
    Quick testing of project service functions
    Run with: python -m app.services.project_service
    """
    import sys
    import os
    
    # Add the backend directory to Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    print("🧪 Testing Project Service...")
    
    try:
        # Test 1: Create a project
        print("\n1️⃣ Testing create_project...")
        test_project = project_service.create_project(
            project_name="Test Project",
            description="This is a test project")
        print(f"✅ Created project: {test_project.project_name} (ID: {test_project.id})")
        
        # Test 2: Get all projects
        print("\n2️⃣ Testing get_projects...")
        projects = project_service.get_projects()
        print(f"✅ Found {len(projects)} projects")
        # ge
        print(projects[0].description)
        
        # Test 3: Get specific project
        print("\n3️⃣ Testing get_project...")
        specific_project = project_service.get_project(test_project.id)
        if specific_project:
            print(f"✅ Retrieved project: {specific_project.project_name}")
        else:
            print("❌ Project not found")
        
        # Test 4: Update project
        print("\n4️⃣ Testing update_project...")
        updated_project = project_service.update_project(
            test_project.id,
            description="Updated description"
        )
        if updated_project:
            print(f"✅ Updated project: {updated_project.project_name}")
        else:
            print("❌ Update failed")
        
        # Test 5: Delete project
        print("\n5️⃣ Testing delete_project...")
        deleted = project_service.delete_project(test_project.id)
        if deleted:
            print("✅ Project deleted successfully")
        else:
            print("❌ Delete failed")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
