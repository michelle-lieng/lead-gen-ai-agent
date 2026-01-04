"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, field_validator
from typing import Optional

def validate_not_empty_string(v: str) -> str:
    """Shared validation: ensure string is not empty or just whitespace"""
    if not v or not v.strip():
        raise ValueError('Field cannot be empty or whitespace only')
    return v.strip()

class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    project_name: str
    description: Optional[str] = None
    
    @field_validator('project_name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure field is not empty or just whitespace"""
        return validate_not_empty_string(v)

class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""
    project_name: Optional[str] = None
    description: Optional[str] = None
    query_search_target: Optional[str] = None
    lead_minimum_criteria: Optional[str] = None  # Required if provided, cannot be removed
    leads_collected: Optional[int] = None
    datasets_added: Optional[int] = None
    urls_processed: Optional[int] = None
    
    @field_validator('lead_minimum_criteria')
    @classmethod
    def validate_lead_minimum_criteria_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If provided, ensure field is not empty or just whitespace. Cannot be set to None to remove it."""
        if v is not None:  # Only validate if field is being updated (not None)
            return validate_not_empty_string(v)
        return v
    
    @field_validator('project_name')
    @classmethod
    def validate_not_empty_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If provided, ensure field is not empty or just whitespace"""
        if v is not None:  # Only validate if field is being updated (not None)
            return validate_not_empty_string(v)
        return v

class ProjectResponse(BaseModel):
    """Schema for project API responses"""
    id: int
    project_name: str
    description: Optional[str] = None
    query_search_target: Optional[str] = None
    lead_minimum_criteria: Optional[str] = None  # Required for new projects and lead extraction, but nullable in DB for backward compatibility
    date_added: str
    last_updated: str
    leads_collected: int
    datasets_added: int
    urls_processed: int
    
    class Config:
        from_attributes = True

class QueryListRequest(BaseModel):
    """Schema for query list requests"""
    queries: list[str]

class QueryGenerationRequest(BaseModel):
    """Schema for AI query generation requests"""
    num_queries: Optional[int] = 3
    
    @field_validator('num_queries')
    @classmethod
    def validate_num_queries(cls, v: Optional[int]) -> int:
        """Validate num_queries is between 1 and 20"""
        if v is None:
            return 3
        if v < 1 or v > 20:
            raise ValueError('num_queries must be between 1 and 20')
        return v

class UrlCreate(BaseModel):
    """Schema for creating a new production URL"""
    link: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None  # Optional date from SERP result
    query: Optional[str] = None  # Optional, will default to "Manual Entry" if not provided
    
    @field_validator('link')
    @classmethod
    def validate_link(cls, v: str) -> str:
        """Ensure link is not empty or just whitespace"""
        return validate_not_empty_string(v)

class UrlUpdate(BaseModel):
    """Schema for updating a production URL"""
    title: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None  # Optional date from SERP result
    link: Optional[str] = None
    
    @field_validator('link')
    @classmethod
    def validate_link_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If link is provided, ensure it's not empty or just whitespace"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Link cannot be empty or whitespace only. Omit the field if you do not want to update it.')
            return v.strip()
        return None

def validate_column_name(v: str) -> str:
    """Validate column name is a valid SQL column name (lowercase, underscores, alphanumeric)"""
    if not v or not v.strip():
        raise ValueError('Column name cannot be empty or whitespace only')
    v = v.strip()
    # Check if it's a valid SQL identifier (lowercase, alphanumeric, underscores only)
    if not v.replace('_', '').isalnum():
        raise ValueError('Column name must contain only lowercase letters, numbers, and underscores')
    if not v.islower():
        raise ValueError('Column name must be lowercase')
    if v[0].isdigit():
        raise ValueError('Column name cannot start with a number')
    return v

class EnrichmentCreate(BaseModel):
    """Schema for creating a new enrichment"""
    enrichment_name: str
    column_name: Optional[str] = None
    enrichment_description: Optional[str] = None
    # Note: project_id comes from URL path, not request body
    
    @field_validator('enrichment_name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure field is not empty or just whitespace"""
        return validate_not_empty_string(v)
    
    @field_validator('column_name')
    @classmethod
    def validate_column_name_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """Validate column name is a valid SQL column name if provided"""
        if v is not None:
            return validate_column_name(v)
        return v

class EnrichmentUpdate(BaseModel):
    """Schema for updating an enrichment - all fields optional"""
    enrichment_name: Optional[str] = None
    column_name: Optional[str] = None
    enrichment_description: Optional[str] = None
    goal: Optional[str] = None
    acceptable_evidence: Optional[str] = None
    result_format: Optional[str] = None
    result_true_if: Optional[str] = None
    result_false_if: Optional[str] = None
    result_number_value: Optional[str] = None
    result_text_value: Optional[str] = None
    
    @field_validator('enrichment_name')
    @classmethod
    def validate_not_empty_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If provided, ensure field is not empty or just whitespace"""
        if v is not None:  # Only validate if field is being updated (not None)
            return validate_not_empty_string(v)
        return v
    
    @field_validator('column_name')
    @classmethod
    def validate_column_name_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If provided, validate column name is a valid SQL column name"""
        if v is not None:  # Only validate if field is being updated (not None)
            return validate_column_name(v)
        return v

class EnrichmentResponse(BaseModel):
    """Schema for enrichment API responses"""
    id: int
    project_id: int
    enrichment_name: str
    column_name: Optional[str] = None
    enrichment_description: Optional[str] = None
    goal: Optional[str] = None
    acceptable_evidence: Optional[str] = None
    result_format: Optional[str] = None
    result_true_if: Optional[str] = None
    result_false_if: Optional[str] = None
    result_number_value: Optional[str] = None
    result_text_value: Optional[str] = None
    date_added: str
    last_updated: str
    
    class Config:
        from_attributes = True

class EnrichLeadsRequest(BaseModel):
    """Schema for enriching leads"""
    enrichment_id: int
    column_name: str  # Column name to use for the enrichment results
    result_format: str
    leads_data: list[dict]  # List of lead dictionaries with at least a "lead" keyclass QueryResponse(BaseModel):
    """Schema for query response"""
    id: int
    project_id: int
    query: str
    date_added: str
    
    class Config:
        from_attributes = True
    
    @field_validator('date_added', mode='before')
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO format string"""
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return v

class UrlResponse(BaseModel):
    """Schema for URL response"""
    id: int
    project_id: int
    query: str
    title: str
    link: str
    snippet: str
    date: Optional[str] = None
    website_scraped: Optional[str] = None
    status: str
    created_at: Optional[str] = None

class UrlGenerationResponse(BaseModel):
    """Schema for URL generation response"""
    urls_added: int
    queries_processed: int

class LeadExtractionResponse(BaseModel):
    """Schema for lead extraction response from SERP URLs"""
    urls_processed: int
    urls_skipped: int
    urls_failed: int
    total_urls_attempted: int
    new_leads_extracted: int
    extracted_leads: list[dict]  # List of extraction results per URL

class MergedResultsResponse(BaseModel):
    """Schema for merged results API response"""
    data: list[dict]  # List of result rows with dynamic columns
    columns: list[str]  # List of column names (base columns + enrichment columns)
    count: int  # Total number of results