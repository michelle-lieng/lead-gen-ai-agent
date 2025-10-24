"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel
from typing import Optional


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    project_name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""
    project_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    leads_collected: Optional[int] = None
    datasets_added: Optional[int] = None


class ProjectResponse(BaseModel):
    """Schema for project API responses"""
    id: int
    project_name: str
    description: Optional[str]
    status: str
    date_added: str
    last_updated: str
    leads_collected: int
    datasets_added: int
    
    class Config:
        from_attributes = True


class QueryListRequest(BaseModel):
    """Schema for query list requests"""
    queries: list[str]