"""
Project overview page
"""
import streamlit as st
from api_client import update_project

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
