"""
Lead utility functions for normalizing and processing lead names
"""
import re


def normalize_lead_name(lead_name: str) -> str:
    """
    Normalize lead name to avoid duplicates from case differences, whitespace, etc.
    
    Normalization steps:
    1. Convert to lowercase
    2. Strip leading/trailing whitespace
    3. Normalize multiple spaces to single space
    4. Remove zero-width characters and other invisible unicode
    
    Args:
        lead_name: Original lead name
        
    Returns:
        str: Normalized lead name (lowercase, trimmed, whitespace normalized)
    """
    if not lead_name:
        return ""
    
    # Convert to string and lowercase
    normalized = str(lead_name).lower()
    
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    
    # Normalize multiple spaces/newlines/tabs to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove zero-width spaces and other problematic unicode characters
    normalized = normalized.encode('utf-8', 'ignore').decode('utf-8')
    normalized = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', normalized)  # Zero-width chars
    
    return normalized.strip()

