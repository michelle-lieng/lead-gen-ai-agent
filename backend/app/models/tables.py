"""
PostgreSQL table models for the AI Lead Generator
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
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

# Future PostgreSQL tables can be added here:
# class Lead(Base):
#     """PostgreSQL table: leads - for storing generated leads"""
#     __tablename__ = "leads"
#     # ... lead fields

# class Dataset(Base):
#     """PostgreSQL table: datasets - for storing lead datasets"""
#     __tablename__ = "datasets"
#     # ... dataset fields
