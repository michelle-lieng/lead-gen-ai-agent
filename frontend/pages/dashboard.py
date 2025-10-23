"""
Dashboard page - main project overview and creation
"""
import streamlit as st
from api_client import get_projects, create_project

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
