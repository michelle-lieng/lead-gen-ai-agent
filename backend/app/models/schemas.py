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
    description: str  # Required field
    
    @field_validator('project_name', 'description')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure field is not empty or just whitespace"""
        return validate_not_empty_string(v)

class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""
    project_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    leads_collected: Optional[int] = None
    datasets_added: Optional[int] = None
    urls_processed: Optional[int] = None
    
    @field_validator('project_name', 'description')
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
    description: str  # Required field
    status: str
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