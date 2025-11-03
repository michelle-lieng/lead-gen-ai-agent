"""
Project overview page
"""
import streamlit as st
from api_client import update_project, delete_project, get_project

def show_project_overview():
    """Project overview page"""
    # Always fetch fresh project data when page loads
    selected_project = st.session_state.selected_project
    if selected_project:
        project = get_project(selected_project['id'])
        if project:
            # Update session state with fresh data
            st.session_state.selected_project = project
        else:
            # Fallback to session state if API call fails
            project = selected_project
    else:
        st.error("No project selected")
        return
    
    st.markdown(f"# 📋 {project['project_name']}")
    st.markdown("---")
    
    # Project stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Leads Collected", project['leads_collected'])
    with col2:
        st.metric("Datasets Added", project['datasets_added'])
    with col3:
        st.metric("URLs Processed", project.get('urls_processed', 0))
    with col4:
        st.metric("Project ID", project['id'])
    
    st.markdown("---")
    
    # Project description
    if project.get('description'):
        st.markdown("### 📝 Description")
        st.write(project['description'])
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Start Lead Collection", use_container_width=True):
            st.session_state.current_page = "collect_leads"
            st.rerun()
    
    with col2:
        if st.button("📋 Review All Leads", use_container_width=True):
            st.session_state.current_page = "review_leads"
            st.rerun()
    
    with col3:
        if st.button("🗑️ Delete Project", use_container_width=True, type="secondary"):
            delete_key = f"show_delete_confirm_{project['id']}"
            st.session_state[delete_key] = True
            st.rerun()
    
    # Check if delete confirmation is active
    delete_key = f"show_delete_confirm_{project['id']}"
    if st.session_state.get(delete_key, False):
        # Show confirmation UI
        st.markdown("---")
        st.warning("⚠️ Are you sure you want to delete this project? This action cannot be undone.")
        confirm_col1, confirm_col2 = st.columns(2)
        with confirm_col1:
            if st.button("✅ Yes, Delete", key="confirm_delete", use_container_width=True, type="primary"):
                with st.spinner("Deleting project..."):
                    success = delete_project(project['id'])
                    if success:
                        st.success(f"✅ Project '{project['project_name']}' deleted successfully!")
                        # Clean up state
                        if delete_key in st.session_state:
                            del st.session_state[delete_key]
                        st.session_state.selected_project = None
                        st.session_state.current_page = "dashboard"
                        st.rerun()
        with confirm_col2:
            if st.button("❌ Cancel", key="cancel_delete", use_container_width=True):
                # Reset confirmation state
                if delete_key in st.session_state:
                    del st.session_state[delete_key]
                st.rerun()
