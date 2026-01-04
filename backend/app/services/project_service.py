"""
Project service for managing project operations
"""
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from typing import List, Optional
import logging

from ..models.tables import Project, SerpUrl, SerpLead, SerpQuery, ProjectDataset, MergedResult
from .database_service import db_service
from ..exceptions import DuplicateProjectNameError, ProjectNotFoundError, InvalidProjectConfigurationError, DatabaseFailureError

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
                    raise DuplicateProjectNameError(project_name)
                
                project = Project(
                    project_name=project_name,
                    description=description)
                session.add(project)
                session.commit() #save data to database
                session.refresh(project) # updates python object with database values to return 
                logger.info(f"✅ Created project: {project_name}")
                return project
        except SQLAlchemyError as e:
            logger.exception("❌ Error creating project")
            raise DatabaseFailureError("Failed to create project") from e
    
    def get_projects(self) -> List[Project]:
        """Get all projects, refreshing counts from database before returning"""
        try:
            # Refresh all project counts first to ensure accuracy
            self.update_project_counts_from_db()  # None = all projects
            
            with db_service.get_session() as session:
                return session.query(Project).order_by(Project.date_added.desc()).all()
        except SQLAlchemyError as e:
            logger.exception("❌ Error getting projects")
            raise DatabaseFailureError("Failed to retrieve projects") from e
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get specific project by ID, refreshing counts from database before returning"""
        try:
            # Refresh project counts first to ensure accuracy
            self.update_project_counts_from_db(project_id)
            
            with db_service.get_session() as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ProjectNotFoundError(project_id)
                return project
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error getting project {project_id}")
            raise DatabaseFailureError(f"Failed to retrieve project {project_id}") from e
    
    def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        """Update project fields"""
        try:
            with db_service.get_session() as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ProjectNotFoundError(project_id)
                
                # Check if project name is being updated and if it already exists
                if 'project_name' in kwargs:
                    new_project_name = kwargs['project_name']
                    # Only check for duplicates if the name is actually changing
                    if new_project_name != project.project_name:
                        existing_project = session.query(Project).filter(
                            Project.project_name == new_project_name,
                            Project.id != project_id
                        ).first()
                        if existing_project:
                            raise DuplicateProjectNameError(new_project_name)
                
                # Prevent removing lead_minimum_criteria - it's required
                if 'lead_minimum_criteria' in kwargs:
                    new_criteria = kwargs['lead_minimum_criteria']
                    if new_criteria is None or (isinstance(new_criteria, str) and not new_criteria.strip()):
                        raise InvalidProjectConfigurationError("lead_minimum_criteria cannot be removed or set to empty. It is required for lead extraction.")
                
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                
                session.commit()
                session.refresh(project)
                logger.info(f"✅ Updated project {project_id}")
                return project
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error updating project {project_id}")
            raise DatabaseFailureError(f"Failed to update project {project_id}") from e
    
    def delete_project(self, project_id: int) -> None:
        """Delete project by ID, including all related records (cascade deletes automatically)"""
        try:
            with db_service.get_session() as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ProjectNotFoundError(project_id)
                
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
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error deleting project {project_id}")
            raise DatabaseFailureError(f"Failed to delete project {project_id}") from e
    
    def update_project_counts_from_db(self, project_id: Optional[int] = None) -> None:
        """
        Recalculate and update project counts from database tables.
        Counts only URLs with status='processed' or 'skip' from serp_urls, total unique leads from merged_results,
        and all datasets from project_datasets.
        
        Args:
            project_id (int, optional): ID of the project to update. If None, updates all projects.
            
        Raises:
            ProjectNotFoundError: If project_id is provided and project is not found
        """
        try:            
            with db_service.get_session() as session:
                if project_id is not None:
                    # Update specific project
                    project = session.query(Project).filter(Project.id == project_id).first()
                    if not project:
                        raise ProjectNotFoundError(project_id)
                    
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
                
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error updating project counts for {project_id if project_id else 'all projects'}")
            raise DatabaseFailureError("Failed to update project counts") from e

# Global project service instance
project_service = ProjectService()
project_service = ProjectService()