"""
Project overview page
"""
import streamlit as st
from api import get_project
from utils.display_errors import call_api

def show_project_overview():
    """Project overview page"""
    # Always fetch fresh project data when page loads
    selected_project = st.session_state.selected_project
    if selected_project:
        project = call_api(get_project, selected_project['id'])
        if project:
            # Update session state with fresh data
            st.session_state.selected_project = project
        else:
            # Fallback to session state if API call fails
            project = selected_project
    else:
        st.error("No project selected")
        return
    
    st.markdown(f"# 📋 Project Overview - {project['project_name']}")
    st.markdown("---")
    
    # Project stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Leads Collected", project['leads_collected'])
    with col2:
        st.metric("Datasets Added", project['datasets_added'])
    with col3:
        st.metric("URLs Processed", project.get('urls_processed', 0))
    
    st.markdown("---")
    
    # Project description
    if project.get('description'):
        st.markdown("### 📝 Description")
        st.write(project['description'])
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Start Lead Collection", width='stretch'):
            st.session_state.current_page = "collect_leads"
            st.rerun()

    with col2:
        if st.button("🔍 Start Lead Enrichment", width='stretch'):
            st.session_state.current_page = "enrichments"
            st.rerun()

    with col3:
        if st.button("📋 Review All Leads", width='stretch'):
            st.session_state.current_page = "review_leads"
            st.rerun()