# backend/app/prompts/__init__.py
"""
System prompts for AI services
"""

from .serp_queries import SERP_QUERIES_PROMPT
from .serp_extraction import SERP_EXTRACTION_PROMPT

__all__ = [
    'SERP_QUERIES_PROMPT',
    'SERP_EXTRACTION_PROMPT'
]