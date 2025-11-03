"""
Dashboard page - main project overview and creation
"""
import streamlit as st
from api_client import get_projects, create_project, delete_project

def show_dashboard():
    """Main dashboard - project overview and creation"""
    st.markdown("# 🤖 AI Lead Generator Dashboard")
    st.markdown("---")
    
    # Create new project section
    st.subheader("🚀 Create New Project")
    
    with st.form("create_project_form"):
        project_name = st.text_input("Project Name", placeholder="e.g., Environmental Leads")
        description = st.text_area("Description", placeholder="Describe your project...", help="Required: Describe your target companies. Be specific about industry, location, company size, and any other criteria")
        
        submitted = st.form_submit_button("Create Project", type="primary")
        
        if submitted:
            if not project_name:
                st.error("Please enter a project name")
            elif not description or not description.strip():
                st.error("Please enter a project description")
            else:
                with st.spinner("Creating project..."):
                    result = create_project(project_name, description)
                    if result:
                        st.success(f"✅ Project '{project_name}' created successfully!")
                        st.rerun()
    
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
                col1, col2, col3, col4, col5, col6 = st.columns([4, 1, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{project['project_name']}**")
                    if project.get('description'):
                        st.caption(f"📝 {project['description']}")
                    
                    # Dates
                    created_date = project['date_added'][:10]
                    updated_date = project['last_updated'][:10]
                    st.caption(f"📅 Created: {created_date} | Updated: {updated_date}")
                
                with col2:
                    st.metric("🎯 Leads", project.get('leads_collected',0))
                
                with col3:
                    st.metric("📊 Datasets", project.get('datasets_added',0))
                
                with col4:
                    st.metric("🔗 URLs", project.get('urls_processed', 0))
                
                with col5:
                    if st.button("🔍 Open", key=f"open_{project['id']}"):
                        st.session_state.selected_project = project
                        st.session_state.current_page = "project_overview"
                        st.rerun()
                
                with col6:
                    delete_key = f"delete_confirm_{project['id']}"
                    # Check if we're in confirmation mode
                    if st.session_state.get(delete_key, False):
                        # Show confirm button instead
                        if st.button("✅ Confirm", key=f"confirm_delete_{project['id']}", help="Confirm deletion"):
                            with st.spinner("Deleting project..."):
                                success = delete_project(project['id'])
                                if success:
                                    st.success(f"✅ Project '{project['project_name']}' deleted successfully!")
                                    # Reset confirmation state
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    # Clear selected project if it was the deleted one
                                    if st.session_state.selected_project and st.session_state.selected_project['id'] == project['id']:
                                        st.session_state.selected_project = None
                                        st.session_state.current_page = "dashboard"
                                    st.rerun()
                        # Cancel button
                        if st.button("❌ Cancel", key=f"cancel_delete_{project['id']}", help="Cancel deletion"):
                            if delete_key in st.session_state:
                                del st.session_state[delete_key]
                            st.rerun()
                    else:
                        # Initial delete button
                        if st.button("🗑️", key=f"delete_{project['id']}", help="Delete project"):
                            st.session_state[delete_key] = True
                            st.rerun()
                
                # Show confirmation message if delete was clicked
                if st.session_state.get(f"delete_confirm_{project['id']}", False):
                    st.warning(f"⚠️ Are you sure you want to delete '{project['project_name']}'? Click Confirm to delete or Cancel to abort.")
                
                st.markdown("---")
