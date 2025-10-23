"""
Streamlit frontend for Lead Gen AI Agent platform
"""
import streamlit as st
import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Your FastAPI backend URL

def get_projects():
    """Fetch projects from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/projects/")
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

def create_project(project_name, description=None):
    """Create a new project via API"""
    try:
        data = {
            "project_name": project_name,
            "description": description
        }
        response = requests.post(f"{API_BASE_URL}/projects/", json=data)
        
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

def main():
    st.set_page_config(
        page_title="AI Lead Generator",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize session state
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        # Dashboard button
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.session_state.selected_project = None
            st.rerun()
        
        st.markdown("---")
        
        # Project selection
        st.markdown("### 📁 Projects")
        projects = get_projects()
        
        if projects:
            for project in projects:
                if st.button(f"📋 {project['project_name']}", key=f"select_{project['id']}", use_container_width=True):
                    st.session_state.selected_project = project
                    st.session_state.current_page = "project_overview"
                    st.rerun()
        else:
            st.info("No projects yet")
        
        st.markdown("---")
        
        # Project-specific navigation (only show if project is selected)
        if st.session_state.selected_project:
            st.markdown("### 🔧 Project Tools")
            
            if st.button("📊 Overview", key="overview", use_container_width=True):
                st.session_state.current_page = "project_overview"
                st.rerun()
            
            if st.button("🎯 Collect Leads", key="collect", use_container_width=True):
                st.session_state.current_page = "collect_leads"
                st.rerun()
            
            if st.button("📋 Review Leads", key="review", use_container_width=True):
                st.session_state.current_page = "review_leads"
                st.rerun()
    
    # Main content area
    if st.session_state.current_page == "dashboard":
        show_dashboard()
    elif st.session_state.current_page == "project_overview":
        show_project_overview()
    elif st.session_state.current_page == "collect_leads":
        show_collect_leads()
    elif st.session_state.current_page == "review_leads":
        show_review_leads()

def show_dashboard():
    """Main dashboard - project overview and creation"""
    st.markdown("# 🤖 AI Lead Generator Dashboard")
    st.markdown("---")
    
    # Create new project section
    st.subheader("🚀 Create New Project")
    
    with st.form("create_project_form"):
        project_name = st.text_input("Project Name", placeholder="e.g., Environmental Leads")
        description = st.text_area("Description (Optional)", placeholder="Describe your project...")
        
        submitted = st.form_submit_button("Create Project", type="primary")
        
        if submitted:
            if project_name:
                with st.spinner("Creating project..."):
                    result = create_project(project_name, description)
                    if result:
                        st.success(f"✅ Project '{project_name}' created successfully!")
                        st.rerun()
            else:
                st.error("Please enter a project name")
    
    st.markdown("---")
    
    # Projects overview
    st.subheader("📁 Your Projects")
    
    with st.spinner("Loading projects..."):
        projects = get_projects()
    
    if not projects:
        st.info("No projects yet. Create your first project above!")
    else:
        st.write(f"**Found {len(projects)} project(s)**")
        st.markdown("---")
        
        for project in projects:
            with st.container():
                # Main project info
                col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{project['project_name']}**")
                    if project.get('description'):
                        st.caption(f"📝 {project['description']}")
                    
                    # Dates
                    created_date = project['date_added'][:10]
                    updated_date = project['last_updated'][:10]
                    st.caption(f"📅 Created: {created_date} | Updated: {updated_date}")
                
                with col2:
                    status = project['status']
                    if status == 'Completed':
                        st.success(f"✅ {status}")
                    elif status == 'In Progress':
                        st.warning(f"🔄 {status}")
                    else:
                        st.info(f"📋 {status}")
                
                with col3:
                    st.metric("🎯 Leads", project['leads_collected'])
                
                with col4:
                    st.metric("📊 Datasets", project['datasets_added'])
                
                with col5:
                    if st.button("🔍 Open", key=f"open_{project['id']}"):
                        st.session_state.selected_project = project
                        st.session_state.current_page = "project_overview"
                        st.rerun()
                
                st.markdown("---")

def show_project_overview():
    """Project overview page"""
    project = st.session_state.selected_project
    st.markdown(f"# 📋 {project['project_name']}")
    st.markdown("---")
    
    # Project stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Status", project['status'])
    with col2:
        st.metric("Leads Collected", project['leads_collected'])
    with col3:
        st.metric("Datasets Added", project['datasets_added'])
    with col4:
        st.metric("Project ID", project['id'])
    
    st.markdown("---")
    
    # Project description
    if project.get('description'):
        st.markdown("### 📝 Description")
        st.write(project['description'])
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Start Lead Collection", use_container_width=True):
            st.session_state.current_page = "collect_leads"
            st.rerun()
    
    with col2:
        if st.button("📋 Review All Leads", use_container_width=True):
            st.session_state.current_page = "review_leads"
            st.rerun()

def show_collect_leads():
    """Lead collection page"""
    project = st.session_state.selected_project
    st.markdown(f"# 🎯 Collect Leads - {project['project_name']}")
    st.markdown("---")
    
    st.markdown("### 🔍 Lead Collection Tools")
    
    # Lead collection methods - 3 ways to collect leads
    tab1, tab2, tab3 = st.tabs(["🌐 Web Search", "📧 Email Scraping", "📁 Upload Dataset"])
    
    with tab1:
        st.markdown("#### Search for companies online")
        search_query = st.text_input("Search Query", placeholder="e.g., sustainable energy companies in California")
        if st.button("🔍 Search Web"):
            st.info("🔍 Searching the web for leads...")
            # TODO: Implement web search functionality
    
    with tab2:
        st.markdown("#### Extract emails from websites")
        website_url = st.text_input("Website URL", placeholder="https://example.com")
        if st.button("📧 Extract Emails"):
            st.info("📧 Extracting emails from website...")
            # TODO: Implement email extraction
    
    with tab3:
        st.markdown("#### Upload existing dataset")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file with company data",
            key="dataset_upload"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            # Preview data
            if st.button("👀 Preview Data"):
                st.markdown("#### 📊 Data Preview")
                st.info("Preview functionality coming soon!")
        
        st.markdown("---")
        st.markdown("#### 📋 Existing Datasets")
        st.info("No datasets uploaded yet. Upload your first dataset above!")
    
    st.markdown("---")
    st.markdown("### 📊 Current Leads")
    st.info("No leads collected yet. Use the tools above to start collecting leads!")

def show_review_leads():
    """Review leads page"""
    project = st.session_state.selected_project
    st.markdown(f"# 📋 Review Leads - {project['project_name']}")
    st.markdown("---")
    
    st.markdown("### 📊 Combined Leads Table")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "New", "Contacted", "Qualified", "Converted"])
    with col2:
        source_filter = st.selectbox("Filter by Source", ["All", "Web Search", "Email Scraping", "Dataset"])
    with col3:
        st.markdown("### 🔄")
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Leads table
    st.markdown("### 📋 All Leads")
    st.info("No leads available yet. Start collecting leads or upload datasets to see them here!")
    
    # Export options
    st.markdown("---")
    st.markdown("### 📤 Export Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export to CSV"):
            st.info("Export functionality coming soon!")
    with col2:
        if st.button("📧 Export Email List"):
            st.info("Email export coming soon!")
    with col3:
        if st.button("📋 Generate Report"):
            st.info("Report generation coming soon!")

if __name__ == "__main__":
    main()

