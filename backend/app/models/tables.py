"""
PostgreSQL table models for the AI Lead Generator
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Base class for all PostgreSQL tables
Base = declarative_base()

class Project(Base):
    """PostgreSQL table: projects - for managing lead generation projects"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False, unique=True)  # Added unique constraint
    description = Column(Text, nullable=True) # Used for notes
    query_search_target = Column(Text, nullable=True) # Used to generate query prompts
    lead_minimum_criteria = Column(Text, nullable=True) # Used to filter leads during extraction (e.g., "Companies with ESG reports", "B-Corp certified", "sushi company", "pilling company"). Required at application level for lead extraction.
    date_added = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    leads_collected = Column(Integer, default=0)
    datasets_added = Column(Integer, default=0)
    urls_processed = Column(Integer, default=0)
    example_prompts = Column(JSON, nullable=True)  # Example first messages for the chat, written for this project

    # Relationship to serp_queries, serp_urls, and serp_leads
    serp_queries = relationship("SerpQuery", back_populates="project", cascade="all, delete-orphan")
    serp_urls = relationship("SerpUrl", back_populates="project", cascade="all, delete-orphan")
    serp_leads = relationship("SerpLead", back_populates="project", cascade="all, delete-orphan")
    serp_leads_aggregated = relationship("SerpLeadAggregated", back_populates="project", cascade="all, delete-orphan")
    project_datasets = relationship("ProjectDataset", back_populates="project", cascade="all, delete-orphan")
    merged_results = relationship("MergedResult", back_populates="project", cascade="all, delete-orphan")
    enrichments = relationship("Enrichment", back_populates="project", cascade="all, delete-orphan")
    chat_entries = relationship("ChatEntry", back_populates="project", cascade="all, delete-orphan")

class SerpQuery(Base):
    """PostgreSQL table: serp_queries - for generating search questions"""
    __tablename__ = "serp_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    query = Column(Text)
    date_added = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to project
    project = relationship("Project", back_populates="serp_queries")

class SerpUrl(Base):
    """PostgreSQL table: serp_urls - for storing search result SERP URLs"""
    __tablename__ = "serp_urls"
    __table_args__ = (
        UniqueConstraint('project_id', 'link', name='uq_serp_urls_project_link'),  # Unique URL per project
    )
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    query = Column(Text, nullable=False)  # original search query
    title = Column(Text)  # title of the result
    link = Column(Text)  # final URL (unique per project via composite constraint)
    snippet = Column(Text)  # snippet/description from search
    date = Column(Text, nullable=True)  # date from SERP result (optional, e.g., "Oct 9, 2025")
    website_scraped = Column(Text)  # website scraped status
    status = Column(String(50), default="unprocessed")  # processing status
    created_at = Column(DateTime, default=datetime.utcnow)  # creation timestamp
    
    # Relationship back to project and forward to leads
    project = relationship("Project", back_populates="serp_urls")
    serp_leads = relationship("SerpLead", back_populates="serp_url", cascade="all, delete-orphan")

class SerpLead(Base):
    """PostgreSQL table: serp_leads - for storing leads extracted from serp urls"""
    __tablename__ = "serp_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    serp_url_id = Column(Integer, ForeignKey("serp_urls.id", ondelete='CASCADE'), nullable=False)  # Foreign key to SerpUrl.id
    lead = Column(Text, nullable=False)  # The extracted lead/company name
    created_at = Column(DateTime, default=datetime.utcnow)  # When the lead was extracted
    
    # Relationships
    project = relationship("Project", back_populates="serp_leads")
    serp_url = relationship("SerpUrl", back_populates="serp_leads")

class SerpLeadAggregated(Base):
    """PostgreSQL table: serp_leads_aggregated - for storing aggregated leads grouped by name with SERP count"""
    __tablename__ = "serp_leads_aggregated"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    leads = Column(Text, nullable=False)  # The lead/company name (grouped)
    serp_count = Column(Integer, nullable=False, default=0)  # Count of distinct SERP URLs this lead appears in
    created_at = Column(DateTime, default=datetime.utcnow)  # When the aggregated record was created
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # When the aggregated record was last updated
    
    # Relationships
    project = relationship("Project", back_populates="serp_leads_aggregated")

class ProjectDataset(Base):
    """PostgreSQL table: project_datasets - metadata linking projects to datasets"""
    __tablename__ = "project_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    dataset_name = Column(String(255), nullable=False)  # User-friendly name
    lead_column = Column(String(100), nullable=False)  # Which column contains leads (e.g., "company_name")
    enrichment_column_list = Column(Text, nullable=False)  # Which column(s) for enrichment - can be single column or comma-separated list
    row_count = Column(Integer, default=0)  # Number of rows in the dataset
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="project_datasets")
    datasets = relationship("Dataset", back_populates="project_dataset", cascade="all, delete-orphan")

class Dataset(Base):
    """PostgreSQL table: datasets - actual dataset rows with lead and enrichment values"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_dataset_id = Column(Integer, ForeignKey("project_datasets.id", ondelete='CASCADE'), nullable=False)  # Foreign key to ProjectDataset.id
    lead = Column(Text, nullable=False)  # The lead value from lead_column (e.g., company name)
    enrichment_value = Column(Text)  # The enrichment value - stored as text for flexibility (can be int, bool, float, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project_dataset = relationship("ProjectDataset", back_populates="datasets")

# Columns merged_results always has; no research or imported column may take
# one of these names.
BUILT_IN_RESULT_COLUMNS = frozenset({"id", "project_id", "lead", "serp_count"})


class MergedResult(Base):
    """PostgreSQL table: merged_results - for storing merged leads from SERP and datasets with enrichment columns"""
    __tablename__ = "merged_results"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    lead = Column(Text, nullable=False)  # The lead/company name (normalized, case-insensitive, unique per project)
    serp_count = Column(Integer, nullable=True, default=0)  # SERP count from aggregated leads
    
    # Relationships
    project = relationship("Project", back_populates="merged_results")
    
    # Note: Enrichment columns (bcorp_score, sustainability_rating, etc.) are added dynamically
    # via ALTER TABLE when datasets are uploaded. They are not defined in the model.

class Enrichment(Base):
    """PostgreSQL table: enrichments - for storing enrichment configurations"""
    __tablename__ = "enrichments"
    __table_args__ = (
        UniqueConstraint('project_id', 'enrichment_name', name='uq_enrichments_project_name'),  # Unique enrichment name per project
        UniqueConstraint('project_id', 'column_name', name='uq_enrichments_project_column'),  # Unique column name per project
    )
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    enrichment_name = Column(String(255), nullable=False)  # Display name (e.g., "More than 1 doctor") - unique per project
    column_name = Column(String(255), nullable=True)  # Database column name (e.g., "more_than_1_doctor") - unique per project (optional, can be set later)
    enrichment_description = Column(Text, nullable=True)  # User notes/description
    goal = Column(Text, nullable=True)  # Goal description for the enrichment
    acceptable_evidence = Column(Text, nullable=True)  # Description of acceptable evidence
    result_format = Column(String(50), nullable=True)  # "True/False", "Text", or "Number"
    result_true_if = Column(Text, nullable=True)  # Description of true condition (for bool)
    result_false_if = Column(Text, nullable=True)  # Description of false condition (for bool)
    result_number_value = Column(Text, nullable=True)  # Description of number value (for int)
    result_text_value = Column(Text, nullable=True)  # Description of text value (for str)
    date_added = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="enrichments")

class Jobs(Base):
    """PostgreSQL table: jobs - for storing jobs and their status"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False)  # Foreign key to Project.id
    job_type = Column(String(255), nullable=False)  # Type of job (e.g., "generate_leads", "generate_urls" "leads_dataset", "enrichments", "test_enrichments")
    job_type_id = Column(Integer, nullable=True)  # enrichment_id if enrichments pr test_enrichments else null
    status = Column(String(50), default="running")  # Status of the job (e.g., "running", "completed", "failed")
    created_at = Column(DateTime, default=datetime.utcnow)  # When the job started
    completed_at = Column(DateTime, nullable=True)  # When the job was completed
    error_message = Column(Text, nullable=True)  # Error message if the job failed

class ChatEntry(Base):
    """PostgreSQL table: chat_entries - the project's single agent conversation.

    Each project has exactly one thread. User messages, agent replies and run
    log lines all land here in order, so reopening a project resumes it.
    """
    __tablename__ = "chat_entries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    role = Column(String(20), nullable=False)  # "user", "agent" or "log"
    kind = Column(String(30), nullable=False, default="text")  # "text", "step", "result", "error", "breakdown", "definition", "query"
    text = Column(Text, nullable=False, default="")
    payload = Column(JSON, nullable=True)  # Structured extras, e.g. breakdown chips or counts

    project = relationship("Project", back_populates="chat_entries")
