"""
API client for communicating with FastAPI backend
"""
import requests
import streamlit as st
from typing import List, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Your FastAPI backend URL

def get_projects():
    """Fetch projects from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/projects/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch projects: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure your FastAPI server is running on http://localhost:8000")
        return []
    except Exception as e:
        st.error(f"Error fetching projects: {str(e)}")
        return []

def create_project(project_name: str, description: str = None):
    """Create a new project via API"""
    try:
        data = {
            "project_name": project_name,
            "description": description
        }
        response = requests.post(f"{API_BASE_URL}/api/projects/", json=data)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 409:
            st.error(f"Project name '{project_name}' already exists!")
            return None
        else:
            st.error(f"Failed to create project: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure your FastAPI server is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Error creating project: {str(e)}")
        return None

def update_project(project_id: int, **kwargs):
    """Update project via API"""
    try:
        data = {k: v for k, v in kwargs.items() if v is not None}
        response = requests.put(f"{API_BASE_URL}/api/projects/{project_id}", json=data)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.error(f"Project {project_id} not found!")
            return None
        else:
            st.error(f"Failed to update project: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure your FastAPI server is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Error updating project: {str(e)}")
        return None

def get_project(project_id: int):
    """Get specific project by ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/projects/{project_id}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.error(f"Project {project_id} not found!")
            return None
        else:
            st.error(f"Failed to fetch project: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure your FastAPI server is running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Error fetching project: {str(e)}")
        return None

def delete_project(project_id: int):
    """Delete project via API"""
    try:
        response = requests.delete(f"{API_BASE_URL}/api/projects/{project_id}")
        
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            st.error(f"Project {project_id} not found!")
            return False
        else:
            st.error(f"Failed to delete project: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure your FastAPI server is running on http://localhost:8000")
        return False
    except Exception as e:
        st.error(f"Error deleting project: {str(e)}")
        return False
