"""
API client for communicating with FastAPI backend

This package is organized to match the backend route structure:
- projects.py → backend/app/api/routes/projects.py
- leads_serp.py → backend/app/api/routes/leads_serp.py
- leads_dataset.py → backend/app/api/routes/leads_dataset.py
- merged_results.py → backend/app/api/routes/merged_results.py
- enrichments.py → backend/app/api/routes/enrichments.py

All functions are re-exported here for convenient imports:
    from api import create_project, get_enrichments, etc.
"""

# Re-export all functions from individual modules
from .projects import (
    get_projects,
    create_project,
    get_project,
    update_project,
    delete_project
)

from .leads_serp import (
    generate_queries,
    get_queries,
    generate_urls,
    get_urls,
    create_url,
    update_url,
    delete_url,
    generate_leads,
    fetch_latest_run_zip
)

from .leads_dataset import (
    upload_dataset
)

from .merged_results import (
    get_merged_results,
    fetch_merged_results_zip
)

from .enrichments import (
    create_enrichment,
    get_enrichments,
    get_enrichment,
    update_enrichment,
    delete_enrichment,
    enrich_leads,
    test_enrich_leads
)

# Export all for convenience
__all__ = [
    # Projects
    'get_projects',
    'create_project',
    'get_project',
    'update_project',
    'delete_project',
    # SERP Leads
    'generate_queries',
    'get_queries',
    'generate_urls',
    'get_urls',
    'create_url',
    'update_url',
    'delete_url',
    'generate_leads',
    'fetch_latest_run_zip',
    # Dataset
    'upload_dataset',
    # Merged Results
    'get_merged_results',
    'fetch_merged_results_zip',
    # Enrichments
    'create_enrichment',
    'get_enrichments',
    'get_enrichment',
    'update_enrichment',
    'delete_enrichment',
    'enrich_leads',
    'test_enrich_leads',
]

