"""
Job service for managing job operations
"""
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import logging
from datetime import datetime

from ..models.tables import Jobs
from .database_service import db_service
from ..exceptions import DatabaseFailureError, JobNotFoundError, JobAlreadyRunningError

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
                job = session.query(Jobs).filter(Jobs.project_id == project_id, Jobs.job_type == job_type, Jobs.job_type_id == job_type_id, Jobs.status == "running").first()
                if job:
                    raise JobAlreadyRunningError(job.id)
                return None
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error getting running jobs for project {project_id} and job type {job_type}")
            raise DatabaseFailureError(f"Failed to get running jobs for project {project_id} and job type {job_type}") from e
        
    def mark_job_as_completed(self, job_id: int) -> Jobs:
        """Update a job completed at"""
        try:
            with db_service.get_session() as session:
                job = session.query(Jobs).filter(Jobs.id == job_id).first()
                if not job:
                    raise JobNotFoundError(job_id)
                job.status = "completed"
                job.completed_at = datetime.now()
                session.commit()
                session.refresh(job)
                logger.info(f"✅ Updated job to completed: for job {job_id}")
                return job
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error updating job completed : for job {job_id}")
            raise DatabaseFailureError(f"Failed to update job completed: for job {job_id}") from e
        
    def mark_job_as_failed(self, job_id: int, error_message: str) -> Jobs:
        """Mark a job as failed"""
        try:
            with db_service.get_session() as session:
                job = session.query(Jobs).filter(Jobs.id == job_id).first()
                if not job:
                    raise JobNotFoundError(job_id)
                job.status = "failed"
                job.error_message = error_message
                job.completed_at = datetime.now()
                session.commit()
                session.refresh(job)
                logger.info(f"✅ Marked job as failed: {error_message} for job {job_id}")
                return job
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error marking job as failed: {error_message} for job {job_id}")
            raise DatabaseFailureError(f"Failed to mark job as failed: {error_message} for job {job_id}") from e

    def mark_all_running_jobs_as_failed(self, error_message: str = "Server restarted - job marked as failed") -> int:
        """
        Mark all running jobs as failed. Called on server startup to clean up
        jobs that were left in 'running' state due to server crash or shutdown.
        
        Args:
            error_message: Error message to set for all failed jobs
            
        Returns:
            int: Number of jobs marked as failed
        """
        try:
            with db_service.get_session() as session:
                running_jobs = session.query(Jobs).filter(Jobs.status == "running").all()
                
                if not running_jobs:
                    logger.info("ℹ️ No running jobs found to mark as failed")
                    return 0
                
                count = 0
                for job in running_jobs:
                    job.status = "failed"
                    job.error_message = error_message
                    job.completed_at = datetime.now()
                    count += 1
                
                session.commit()
                logger.info(f"✅ Marked {count} running job(s) as failed on server startup")
                return count
                
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error marking running jobs as failed on startup")
            # Don't raise - allow server to start even if this fails
            return 0

job_service = JobService()