"""
Custom exceptions for the application
"""

# =========================
# Project domain errors
# =========================

class ProjectError(Exception):
    """Base exception for project-related errors"""
    status_code = 400
    code = "PROJECT_ERROR"

    def __init__(self, message: str):
        super().__init__(message)

class DuplicateProjectNameError(ProjectError):
    """Raised when trying to create/update a project with a name that already exists"""
    status_code = 409
    code = "DUPLICATE_PROJECT_NAME"

    def __init__(self, project_name: str):
        message = f"Project name '{project_name}' already exists"
        super().__init__(message)

class ProjectNotFoundError(ProjectError):
    """Raised when a project is not found"""
    status_code = 404
    code = "PROJECT_NOT_FOUND"
    
    def __init__(self, project_id: int):
        message = f"Project with ID {project_id} not found"
        super().__init__(message)

class InvalidProjectConfigurationError(ProjectError):
    """Raised when project configuration is invalid"""
    status_code = 400
    code = "INVALID_PROJECT_CONFIGURATION"

# =========================
# Dataset / file validation errors
# =========================

class InvalidFileError(Exception):
    """Raised when file validation fails (e.g., empty file, invalid format)"""
    status_code = 400
    code = "INVALID_FILE"
    
    def __init__(self, message: str = "Invalid file"):
        super().__init__(message)

class InvalidEnrichmentColumnError(Exception):
    """Raised when enrichment column validation fails (e.g., missing columns, invalid format)"""
    status_code = 400
    code = "INVALID_ENRICHMENT_COLUMN"
    
    def __init__(self, message: str = "Invalid enrichment column"):
        super().__init__(message)

class ProjectDatasetNotFoundError(Exception):
    """Raised when a ProjectDataset is not found"""
    status_code = 404
    code = "PROJECT_DATASET_NOT_FOUND"
    
    def __init__(self, project_dataset_id: int):
        message = f"ProjectDataset with ID {project_dataset_id} not found"
        super().__init__(message)

# =========================
# URL domain errors
# =========================

class UrlError(Exception):
    """Base exception for URL-related errors"""
    status_code = 400
    code = "URL_ERROR"
    
    def __init__(self, message: str):
        super().__init__(message)

class UrlNotFoundError(UrlError):
    """Raised when a URL is not found"""
    status_code = 404
    code = "URL_NOT_FOUND"
    
    def __init__(self, url_id: int, project_id: int):
        message = f"URL with ID {url_id} not found for project {project_id}"
        super().__init__(message)

class DuplicateUrlError(UrlError):
    """Raised when trying to create/update a URL that already exists in the project"""
    status_code = 409
    code = "DUPLICATE_URL"
    
    def __init__(self, link: str, project_id: int):
        message = f"URL already exists in this project: {link}"
        super().__init__(message)

# =========================
# Infrastructure / system errors
# =========================

class DatabaseFailureError(Exception):
    """Raised when a database operation fails"""
    status_code = 500
    code = "DATABASE_FAILURE"
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message)

class ApiKeyNotConfiguredError(Exception):
    """Raised when a required API key is not configured"""
    status_code = 500
    code = "API_KEY_NOT_CONFIGURED"
    
    def __init__(self, message: str = "Required API key is not configured"):
        super().__init__(message)

# =========================
# External API / scraper errors
# =========================

class ExternalScraperError(Exception):
    """Raised when an external scraper API fails (e.g., Jina SERP, Jina URL scraper)"""
    status_code = 502
    code = "EXTERNAL_SCRAPER_ERROR"
    
    def __init__(self, message: str = "External scraper API failed"):
        super().__init__(message)

class OpenAITokenLimitExceededError(Exception):
    """Raised when OpenAI request exceeds token limit even after truncation attempts"""
    status_code = 413
    code = "OPENAI_TOKEN_LIMIT_EXCEEDED"
    
    def __init__(self, message: str = "OpenAI token limit exceeded"):
        super().__init__(message)

# =========================
# Enrichment domain errors
# =========================

class EnrichmentError(Exception):
    """Base exception for enrichment-related errors"""
    status_code = 400
    code = "ENRICHMENT_ERROR"
    
    def __init__(self, message: str):
        super().__init__(message)

class DuplicateEnrichmentNameError(EnrichmentError):
    """Raised when trying to create an enrichment with a name that already exists"""
    status_code = 409
    code = "DUPLICATE_ENRICHMENT_NAME"
    
    def __init__(self, enrichment_name: str):
        message = f"Enrichment name '{enrichment_name}' already exists"
        super().__init__(message)

class DuplicateEnrichmentColumnNameError(EnrichmentError):
    """Raised when trying to create an enrichment with a column name that already exists"""
    status_code = 409
    code = "DUPLICATE_COLUMN_NAME"
    
    def __init__(self, column_name: str):
        message = f"Column name '{column_name}' already exists"
        super().__init__(message)

class EnrichmentNotFoundError(EnrichmentError):
    """Raised when an enrichment is not found"""
    status_code = 404
    code = "ENRICHMENT_NOT_FOUND"
    
    def __init__(self, enrichment_id: int):
        message = f"Enrichment with ID {enrichment_id} not found"
        super().__init__(message)

class EnrichmentExecutionError(EnrichmentError):
    """Raised when enrichment execution fails for a specific lead"""
    status_code = 500
    code = "ENRICHMENT_EXECUTION_ERROR"
    
    def __init__(self, company_name: str, reason: str):
        message = f"Failed to enrich '{company_name}': {reason}"
        super().__init__(message)
        self.company_name = company_name
        self.reason = reason