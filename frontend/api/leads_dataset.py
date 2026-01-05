"""
Dataset management API client
Matches backend/app/api/routes/leads_dataset.py
"""

import json
from .base import _request


def upload_dataset(project_id: int, dataset_name: str, lead_column: str, enrichment_column_list: list[str], enrichment_column_exists: bool, file):
    """Upload a CSV or Excel dataset for a project via API"""
    file.seek(0)
    file_content = file.read()
    file.seek(0)
    
    # Determine MIME type based on file extension
    filename_lower = file.name.lower()
    if filename_lower.endswith('.xlsx'):
        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif filename_lower.endswith('.xls'):
        mime_type = 'application/vnd.ms-excel'
    else:
        mime_type = 'text/csv'
    
    files = {'file': (file.name, file_content, mime_type)}
    form_data = {
        'dataset_name': dataset_name,
        'lead_column': lead_column,
        'enrichment_column_list': json.dumps(enrichment_column_list) if enrichment_column_list else '[]',  # Always send a JSON string, even if empty
        'enrichment_column_exists': 'true' if enrichment_column_exists else 'false'
    }
    
    response = _request("POST", f"/api/projects/{project_id}/datasets", files=files, form_data=form_data)
    if response:
        try:
            result = response.json()
            # If status code indicates error, ensure success is False
            if response.status_code >= 400:
                if 'success' not in result:
                    result['success'] = False
            return result
        except:
            # If response is not JSON, return error dict with status code
            return {"success": False, "detail": f"Server error: {response.status_code} - {response.text[:200]}"}
    return {"success": False, "detail": "No response from server"}

