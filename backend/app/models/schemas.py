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
    query_search_target: Optional[str] = None
    lead_features_we_want: Optional[str] = None
    lead_features_to_avoid: Optional[str] = None
    
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
    lead_features_we_want: Optional[str] = None
    lead_features_to_avoid: Optional[str] = None
    leads_collected: Optional[int] = None
    datasets_added: Optional[int] = None
    urls_processed: Optional[int] = None
    
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
    lead_features_we_want: Optional[str] = None
    lead_features_to_avoid: Optional[str] = None
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

class TestQueryRequest(BaseModel):
    query: str

class TestUrlCreate(BaseModel):
    """Schema for creating a new test URL"""
    link: str
    title: Optional[str] = None
    snippet: Optional[str] = None

class TestUrlUpdate(BaseModel):
    title: Optional[str] = None
    snippet: Optional[str] = None
    link: Optional[str] = None
    
    @field_validator('link')
    @classmethod
    def validate_link_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """If link is provided, ensure it's not empty or just whitespace (prevents accidentally clearing the link)"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Link cannot be empty or whitespace only. Omit the field if you do not want to update it.')
            return v.strip()
        return None