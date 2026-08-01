"""
Custom exceptions for the application
"""

from typing import Any, Dict, Optional


class AppError(Exception):
    status_code: int = 400
    code: str = "APP_ERROR"

    def __init__(self, message: str, *, meta: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.meta = meta or {}


# =========================
# Project domain errors
# =========================


class ProjectError(AppError):
    """Base exception for project-related errors"""

    status_code = 400
    code = "PROJECT_ERROR"

    def __init__(self, message: str, *, meta: Optional[Dict[str, Any]] = None):
        super().__init__(message, meta=meta)


class DuplicateProjectNameError(ProjectError):
    """Raised when trying to create/update a project with a name that already exists"""

    status_code = 409
    code = "DUPLICATE_PROJECT_NAME"

    def __init__(self, project_name: str):
        super().__init__(
            f"Project name '{project_name}' already exists",
            meta={"project_name": project_name},
        )


class ProjectNotFoundError(ProjectError):
    """Raised when a project is not found"""

    status_code = 404
    code = "PROJECT_NOT_FOUND"

    def __init__(self, project_id: int):
        super().__init__(
            f"Project with ID {project_id} not found",
            meta={"project_id": project_id},
        )


class InvalidProjectConfigurationError(ProjectError):
    """Raised when project configuration is invalid"""

    status_code = 400
    code = "INVALID_PROJECT_CONFIGURATION"


# =========================
# Dataset / file validation errors
# =========================


class InvalidFileError(AppError):
    """Raised when file validation fails (e.g., empty file, invalid format)"""

    status_code = 400
    code = "INVALID_FILE"

    def __init__(
        self, message: str = "Invalid file", *, meta: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, meta=meta)


class InvalidEnrichmentColumnError(AppError):
    """Raised when enrichment column validation fails (e.g., missing columns, invalid format)"""

    status_code = 400
    code = "INVALID_ENRICHMENT_COLUMN"

    def __init__(
        self,
        message: str = "Invalid enrichment column",
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, meta=meta)


class ProjectDatasetNotFoundError(AppError):
    """Raised when a ProjectDataset is not found"""

    status_code = 404
    code = "PROJECT_DATASET_NOT_FOUND"

    def __init__(self, project_dataset_id: int):
        message = f"ProjectDataset with ID {project_dataset_id} not found"
        super().__init__(message, meta={"project_dataset_id": project_dataset_id})


# =========================
# URL domain errors
# =========================


class UrlError(AppError):
    """Base exception for URL-related errors"""

    status_code = 400
    code = "URL_ERROR"

    def __init__(self, message: str, *, meta: Optional[Dict[str, Any]] = None):
        super().__init__(message, meta=meta)


class UrlNotFoundError(UrlError):
    """Raised when a URL is not found"""

    status_code = 404
    code = "URL_NOT_FOUND"

    def __init__(self, url_id: int, project_id: int):
        message = f"URL with ID {url_id} not found for project {project_id}"
        super().__init__(message, meta={"url_id": url_id, "project_id": project_id})


class DuplicateUrlError(UrlError):
    """Raised when trying to create/update a URL that already exists in the project"""

    status_code = 409
    code = "DUPLICATE_URL"

    def __init__(self, link: str, project_id: int):
        message = f"URL already exists in this project: {link}"
        super().__init__(message, meta={"link": link, "project_id": project_id})


# =========================
# Infrastructure / system errors
# =========================


class DatabaseFailureError(AppError):
    """Raised when a database operation fails"""

    status_code = 500
    code = "DATABASE_FAILURE"

    def __init__(
        self,
        message: str = "Database operation failed",
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, meta=meta)


class ApiKeyNotConfiguredError(AppError):
    """Raised when a required API key is not configured"""

    status_code = 500
    code = "API_KEY_NOT_CONFIGURED"

    def __init__(
        self,
        message: str = "Required API key is not configured",
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, meta=meta)


# =========================
# External API / scraper errors
# =========================


class ExternalScraperError(AppError):
    """Raised when an external scraper API fails (e.g., Jina SERP, Jina URL scraper)"""

    status_code = 502
    code = "EXTERNAL_SCRAPER_ERROR"

    def __init__(
        self,
        message: str = "External scraper API failed",
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, meta=meta)


class ScraperApiKeyError(ExternalScraperError):
    """Raised when the scraper API rejects the caller's key (401/403)"""

    status_code = 401
    code = "SCRAPER_API_KEY_INVALID"

    def __init__(
        self,
        message: str = "Scraper API key was rejected",
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, meta=meta)


class ScraperCreditsExhaustedError(ExternalScraperError):
    """Raised when the scraper API reports the key is out of credits (402)"""

    status_code = 402
    code = "SCRAPER_CREDITS_EXHAUSTED"

    def __init__(
        self,
        message: str = "Scraper API key has no credits remaining",
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, meta=meta)


class OpenAITokenLimitExceededError(AppError):
    """Raised when OpenAI request exceeds token limit even after truncation attempts"""

    status_code = 413
    code = "OPENAI_TOKEN_LIMIT_EXCEEDED"

    def __init__(
        self,
        message: str = "OpenAI token limit exceeded",
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, meta=meta)


# =========================
# Enrichment domain errors
# =========================


class EnrichmentError(AppError):
    """Base exception for enrichment-related errors"""

    status_code = 400
    code = "ENRICHMENT_ERROR"

    def __init__(self, message: str, *, meta: Optional[Dict[str, Any]] = None):
        super().__init__(message, meta=meta)


class DuplicateEnrichmentNameError(EnrichmentError):
    """Raised when trying to create an enrichment with a name that already exists"""

    status_code = 409
    code = "DUPLICATE_ENRICHMENT_NAME"

    def __init__(self, enrichment_name: str):
        message = f"Enrichment name '{enrichment_name}' already exists"
        super().__init__(message, meta={"enrichment_name": enrichment_name})


class DuplicateEnrichmentColumnNameError(EnrichmentError):
    """Raised when trying to create an enrichment with a column name that already exists"""

    status_code = 409
    code = "DUPLICATE_COLUMN_NAME"

    def __init__(self, column_name: str):
        message = f"Column name '{column_name}' already exists"
        super().__init__(message, meta={"column_name": column_name})


class EnrichmentNotFoundError(EnrichmentError):
    """Raised when an enrichment is not found"""

    status_code = 404
    code = "ENRICHMENT_NOT_FOUND"

    def __init__(self, enrichment_id: int):
        message = f"Enrichment with ID {enrichment_id} not found"
        super().__init__(message, meta={"enrichment_id": enrichment_id})


class EmptyEnrichmentFieldError(EnrichmentError):
    """Raised when trying to update an enrichment field with empty/whitespace value"""

    status_code = 400
    code = "EMPTY_ENRICHMENT_FIELD"

    def __init__(self, field_names: list[str]):
        field_names_str = "', '".join(field_names)
        if len(field_names) == 1:
            message = f"Field '{field_names_str}' cannot be empty or whitespace only"
        else:
            message = f"The following fields cannot be empty or whitespace only: '{field_names_str}'"
        super().__init__(
            message,
            meta={"field_names": field_names, "field_names_str": field_names_str},
        )


class IncompleteEnrichmentConfigError(EnrichmentError):
    """Raised when enrichment configuration is incomplete based on result_format"""

    status_code = 400
    code = "INCOMPLETE_ENRICHMENT_CONFIG"

    def __init__(self, result_format: str, missing_fields: list[str]):
        fields_str = "', '".join(missing_fields)
        message = f"Result format '{result_format}' requires the following fields to be filled: '{fields_str}'"
        super().__init__(
            message,
            meta={
                "result_format": result_format,
                "missing_fields": missing_fields,
                "fields_str": fields_str,
            },
        )


class NoLeadsToEnrichError(EnrichmentError):
    """Raised when trying to run enrichment with no leads"""

    status_code = 400
    code = "NO_LEADS_TO_ENRICH"

    def __init__(self):
        message = "Cannot run enrichment: no leads provided. Please add leads before running enrichment."
        super().__init__(message)


# =========================
# Job domain errors
# =========================


class JobError(AppError):
    """Base exception for job-related errors"""

    status_code = 400
    code = "JOB_ERROR"

    def __init__(self, message: str, *, meta: Optional[Dict[str, Any]] = None):
        super().__init__(message, meta=meta)


class JobNotFoundError(JobError):
    """Raised when a job is not found"""

    status_code = 404
    code = "JOB_NOT_FOUND"

    def __init__(self, job_id: int):
        message = f"Job with ID {job_id} not found"
        super().__init__(message, meta={"job_id": job_id})


class JobAlreadyRunningError(JobError):
    """Raised when a job is already running"""

    status_code = 409
    code = "JOB_ALREADY_RUNNING"

    def __init__(self, job_id: int):
        message = f"Job with ID {job_id} is already running"
        super().__init__(message, meta={"job_id": job_id})
