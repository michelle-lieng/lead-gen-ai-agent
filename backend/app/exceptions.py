"""
Custom exceptions for the application
"""


class ProjectError(Exception):
    """Base exception for project-related errors"""
    def __init__(self, message: str):
        super().__init__(message)


class DuplicateProjectNameError(ProjectError):
    """Raised when trying to create/update a project with a name that already exists"""
    def __init__(self, project_name: str):
        message = f"Project name '{project_name}' already exists"
        super().__init__(message)


class ProjectNotFoundError(ProjectError):
    """Raised when a project is not found"""
    def __init__(self, project_id: int):
        message = f"Project with ID {project_id} not found"
        super().__init__(message)


class InvalidProjectConfigurationError(ProjectError):
    """Raised when project configuration is invalid"""
    pass


class DatabaseFailureError(Exception):
    """Raised when a database operation fails"""
    pass


