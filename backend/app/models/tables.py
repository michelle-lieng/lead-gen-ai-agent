"""
PostgreSQL table models for the AI Lead Generator
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Base class for all PostgreSQL tables
Base = declarative_base()

class Project(Base):
    """PostgreSQL table: projects - for managing lead generation projects"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False, unique=True)  # Added unique constraint
    description = Column(Text, nullable=False)  # Required field
    date_added = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    leads_collected = Column(Integer, default=0)
    datasets_added = Column(Integer, default=0)
    urls_processed = Column(Integer, default=0)
    
    # Relationship to serp_queries, serp_urls, and serp_leads
    serp_queries = relationship("SerpQuery", back_populates="project", cascade="all, delete-orphan")
    serp_urls = relationship("SerpUrl", back_populates="project", cascade="all, delete-orphan")
    serp_leads = relationship("SerpLead", back_populates="project", cascade="all, delete-orphan")
    project_datasets = relationship("ProjectDataset", back_populates="project", cascade="all, delete-orphan")

class SerpQuery(Base):
    """PostgreSQL table: serp_queries - for generating search questions"""
    __tablename__ = "serp_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # Foreign key to Project.id
    query = Column(Text)
    date_added = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to project
    project = relationship("Project", back_populates="serp_queries")

class SerpUrl(Base):
    """PostgreSQL table: serp_urls - for storing search result SERP URLs"""
    __tablename__ = "serp_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # Foreign key to Project.id
    query = Column(Text, nullable=False)  # original search query
    title = Column(Text)  # title of the result
    link = Column(Text, unique=True)  # final URL (unique constraint)
    snippet = Column(Text)  # snippet/description from search
    website_scraped = Column(Text)  # website scraped status
    status = Column(String(50), default="unprocessed")  # processing status
    created_at = Column(DateTime, default=datetime.utcnow)  # creation timestamp
    
    # Relationship back to project and forward to leads
    project = relationship("Project", back_populates="serp_urls")
    serp_leads = relationship("SerpLead", back_populates="serp_url")

class SerpLead(Base):
    """PostgreSQL table: serp_leads - for storing leads extracted from serp urls"""
    __tablename__ = "serp_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # Foreign key to Project.id
    serp_url_id = Column(Integer, ForeignKey("serp_urls.id"), nullable=False)  # Foreign key to SerpUrl.id
    lead = Column(Text, nullable=False)  # The extracted lead/company name
    created_at = Column(DateTime, default=datetime.utcnow)  # When the lead was extracted
    
    # Relationships
    project = relationship("Project", back_populates="serp_leads")
    serp_url = relationship("SerpUrl", back_populates="serp_leads")

class ProjectDataset(Base):
    """PostgreSQL table: project_datasets - metadata linking projects to datasets"""
    __tablename__ = "project_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # Foreign key to Project.id
    dataset_name = Column(String(255), nullable=False)  # User-friendly name
    lead_column = Column(String(100), nullable=False)  # Which column contains leads (e.g., "company_name")
    enrichment_column = Column(String(100), nullable=False)  # Which column for enrichment (e.g., "overall_score")
    row_count = Column(Integer, default=0)  # Number of rows in the dataset
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="project_datasets")
    dataset_rows = relationship("Dataset", back_populates="project_dataset", cascade="all, delete-orphan")

class Dataset(Base):
    """PostgreSQL table: datasets - actual dataset rows with lead and enrichment values"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_dataset_id = Column(Integer, ForeignKey("project_datasets.id"), nullable=False)  # Foreign key to ProjectDataset.id
    lead = Column(Text, nullable=False)  # The lead value from lead_column (e.g., company name)
    enrichment_value = Column(Text)  # The enrichment value - stored as text for flexibility (can be int, bool, float, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project_dataset = relationship("ProjectDataset", back_populates="dataset_rows")
