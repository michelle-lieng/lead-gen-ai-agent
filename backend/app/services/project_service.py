"""
Project service for managing project operations
"""
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import logging

from ..models.tables import Project
from .database_service import db_service

logger = logging.getLogger(__name__)

class ProjectService:
    """Service for project-related database operations"""

    def create_project(self, project_name: str, description: str) -> Project:
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
                    description=description
                )
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
        """Get all projects"""
        try:
            with db_service.get_session() as session:
                return session.query(Project).order_by(Project.date_added.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting projects: {e}")
            raise
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get specific project by ID"""
        try:
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
                
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                
                session.commit()
                session.refresh(project)
                logger.info(f"✅ Updated project {project_id}")
                return project
        except SQLAlchemyError as e:
            logger.error(f"❌ Error updating project {project_id}: {e}")
            raise
    
    def delete_project(self, project_id: int) -> bool:
        """Delete project by ID"""
        try:
            with db_service.get_session() as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    logger.warning(f"Project {project_id} not found")
                    return False
                
                session.delete(project)
                session.commit()
                logger.info(f"✅ Deleted project {project_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Error deleting project {project_id}: {e}")
            raise

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
            description="This is a test project"
        )
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
            status="In Progress",
            description="Updated description"
        )
        if updated_project:
            print(f"✅ Updated project: {updated_project.project_name} (Status: {updated_project.status})")
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
