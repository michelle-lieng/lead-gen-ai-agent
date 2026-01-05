"""
Job service for managing job operations
"""
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import logging

from ..models.tables import Jobs
from .database_service import db_service
from ..exceptions import DatabaseFailureError, JobNotFoundError

logger = logging.getLogger(__name__)

class JobService:
    """Service for job-related database operations"""

    def create_job(self, 
        project_id: int, 
        job_type: str, 
        job_type_id: Optional[int] = None) -> Jobs:
        """Create a new job"""
        try:
            with db_service.get_session() as session:
                job = Jobs(
                    project_id=project_id,
                    job_type=job_type,
                    job_type_id=job_type_id)
                session.add(job)
                session.commit()
                session.refresh(job)
                logger.info(f"✅ Created job: {job_type} for project {project_id}")
                return job
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error creating job: {job_type} for project {project_id}")
            raise DatabaseFailureError(f"Failed to create job: {job_type} for project {project_id}") from e
        
    def get_jobs(self, project_id: int) -> List[Jobs]:
        """Get all jobs for a project"""
        try:
            with db_service.get_session() as session:
                jobs = session.query(Jobs).filter(Jobs.project_id == project_id).all()
                return jobs
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error getting jobs for project {project_id}")
            raise DatabaseFailureError(f"Failed to get jobs for project {project_id}") from e

    def get_job(self, job_id: int) -> Jobs:
        """Get a job by ID"""
        try:
            with db_service.get_session() as session:
                job = session.query(Jobs).filter(Jobs.id == job_id).first()
                if not job:
                    raise JobNotFoundError(job_id)
                return job
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error getting job {job_id}")
            raise DatabaseFailureError(f"Failed to get job {job_id}") from e
        
    def check_running_job(self, project_id: int, job_type: str, job_type_id: Optional[int] = None) -> Jobs:
        """Get all running jobs for a project and job type"""
        try:
            with db_service.get_session() as session:
                jobs = session.query(Jobs).filter(Jobs.project_id == project_id, Jobs.job_type == job_type, Jobs.job_type_id == job_type_id, Jobs.status == "running").all()
                return jobs
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error getting running jobs for project {project_id} and job type {job_type}")
            raise DatabaseFailureError(f"Failed to get running jobs for project {project_id} and job type {job_type}") from e
        