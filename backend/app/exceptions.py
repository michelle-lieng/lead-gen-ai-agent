"""
Custom exceptions for the application
"""

# =========================
# Project domain errors
# =========================

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

# =========================
# Dataset / file validation errors
# =========================

class InvalidFileError(Exception):
    """Raised when file validation fails (e.g., empty file, invalid format)"""
    pass

class InvalidEnrichmentColumnError(Exception):
    """Raised when enrichment column validation fails (e.g., missing columns, invalid format)"""
    pass

class ProjectDatasetNotFoundError(Exception):
    """Raised when a ProjectDataset is not found"""
    def __init__(self, project_dataset_id: int):
        message = f"ProjectDataset with ID {project_dataset_id} not found"
        super().__init__(message)

# =========================
# URL domain errors
# =========================

class UrlError(Exception):
    """Base exception for URL-related errors"""
    def __init__(self, message: str):
        super().__init__(message)

class UrlNotFoundError(UrlError):
    """Raised when a URL is not found"""
    def __init__(self, url_id: int, project_id: int):
        message = f"URL with ID {url_id} not found for project {project_id}"
        super().__init__(message)

class DuplicateUrlError(UrlError):
    """Raised when trying to create/update a URL that already exists in the project"""
    def __init__(self, link: str, project_id: int):
        message = f"URL already exists in this project: {link}"
        super().__init__(message)

# =========================
# Infrastructure / system errors
# =========================

class DatabaseFailureError(Exception):
    """Raised when a database operation fails"""
    pass

class ApiKeyNotConfiguredError(Exception):
    """Raised when a required API key is not configured"""
    pass

# =========================
# External API / scraper errors
# =========================

class ExternalScraperError(Exception):
    """Raised when an external scraper API fails (e.g., Jina SERP, Jina URL scraper)"""
    pass

class OpenAITokenLimitExceededError(Exception):
    """Raised when OpenAI request exceeds token limit even after truncation attempts"""
    pass