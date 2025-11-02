"""
API client for communicating with FastAPI backend
"""
import requests
import streamlit as st
from typing import List, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Your FastAPI backend URL

def _handle_response(response: requests.Response, success_return=None):
    """Helper to handle API responses consistently"""
    if response.status_code == 200:
        return response.json() if success_return is None else success_return
    
    # Handle error responses - safely extract error message
    try:
        error_data = response.json()
        error_detail = error_data.get('detail', f'Error: {response.status_code}')
    except (ValueError, KeyError):
        # Response is not JSON or doesn't have expected structure
        error_detail = f'HTTP {response.status_code}: {response.text[:100]}'
    
    st.error(f"❌ {error_detail}")
    return None

def _make_request(method: str, url: str, json_data=None, success_return=None):
    """Helper to make API requests with consistent error handling"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=json_data)
        elif method == "PUT":
            response = requests.put(url, json=json_data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        return _handle_response(response, success_return)
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure your FastAPI server is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

def get_projects():
    """Fetch projects from the API"""
    result = _make_request("GET", f"{API_BASE_URL}/api/projects/")
    return result if result is not None else []

def create_project(project_name: str, description: str = None):
    """Create a new project via API"""
    data = {
        "project_name": project_name,
        "description": description
    }
    return _make_request("POST", f"{API_BASE_URL}/api/projects/", json_data=data)

def update_project(project_id: int, **kwargs):
    """Update project via API"""
    data = {k: v for k, v in kwargs.items() if v is not None}
    return _make_request("PUT", f"{API_BASE_URL}/api/projects/{project_id}", json_data=data)

def get_project(project_id: int):
    """Get specific project by ID"""
    return _make_request("GET", f"{API_BASE_URL}/api/projects/{project_id}")

def delete_project(project_id: int):
    """Delete project via API"""
    return _make_request("DELETE", f"{API_BASE_URL}/api/projects/{project_id}", success_return=True) or False

def generate_queries(project_id: int):
    """Generate search queries for a project via API"""
    return _make_request("POST", f"{API_BASE_URL}/api/projects/{project_id}/leads/serp/queries")