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
    description = Column(Text)
    status = Column(String(50), default="Draft")  # Draft, In Progress, Completed
    date_added = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    leads_collected = Column(Integer, default=0)
    datasets_added = Column(Integer, default=0)
    
    # Relationship to queries and initial_urls
    queries = relationship("Queries", back_populates="project")
    initial_urls = relationship("InitialUrls", back_populates="project")

class Queries(Base):
    """PostgreSQL table: queries - for generating search questions"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # Foreign key to Project.id
    query = Column(Text)
    date_added = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to project
    project = relationship("Project", back_populates="queries")

class InitialUrls(Base):
    """PostgreSQL table: initial_urls - for storing search result URLs"""
    __tablename__ = "initial_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # Foreign key to Project.id
    query = Column(Text, nullable=False)  # original search query
    title = Column(Text)  # title of the result
    link = Column(Text, unique=True)  # final URL (unique constraint)
    snippet = Column(Text)  # snippet/description from search
    source = Column(Text)  # domain or source field
    website_scraped = Column(Text)  # website scraped status
    status = Column(String(50), default="unprocessed")  # processing status
    created_at = Column(DateTime, default=datetime.utcnow)  # creation timestamp
    
    # Relationship back to project
    project = relationship("Project", back_populates="initial_urls")

# Future PostgreSQL tables can be added here:
# class Lead(Base):
#     """PostgreSQL table: leads - for storing generated leads"""
#     __tablename__ = "leads"
#     # ... lead fields

# class Dataset(Base):
#     """PostgreSQL table: datasets - for storing lead datasets"""
#     __tablename__ = "datasets"
#     # ... dataset fields
