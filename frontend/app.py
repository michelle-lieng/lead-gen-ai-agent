"""
Main Streamlit application entry point
"""
import streamlit as st
from streamlit_pages.dashboard import show_dashboard
from streamlit_pages.project_overview import show_project_overview
from streamlit_pages.collect_leads import show_collect_leads
from streamlit_pages.review_leads import show_review_leads
from streamlit_pages.test_prompts import show_test_prompts

def init_session_state():
    """Initialize global session state variables"""
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"

def main():
    st.set_page_config(
        page_title="AI Lead Generator",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        # Dashboard button
        if st.button("🏠 Dashboard", width='stretch'):
            st.session_state.current_page = "dashboard"
            st.session_state.selected_project = None
            st.rerun()
        
        st.markdown("---")
        
        # Project selection
        st.markdown("### 📁 Projects")
        from api_client import get_projects
        projects = get_projects()
        
        if projects:
            for project in projects:
                if st.button(f"📋 {project['project_name']}", key=f"select_{project['id']}", width='stretch'):
                    st.session_state.selected_project = project
                    st.session_state.current_page = "project_overview"
                    st.rerun()
        else:
            st.info("No projects yet")
        
        st.markdown("---")
        
        # Project-specific navigation (only show if project is selected)
        if st.session_state.selected_project:
            st.markdown("### 🔧 Project Tools")
            
            if st.button("📊 Overview", key="overview", width='stretch'):
                st.session_state.current_page = "project_overview"
                st.rerun()
            
            if st.button("🎯 Collect Leads", key="collect", width='stretch'):
                st.session_state.current_page = "collect_leads"
                st.rerun()
            
            if st.button("📋 Review Leads", key="review", width='stretch'):
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
    elif st.session_state.current_page == "test_prompts":
        show_test_prompts()

if __name__ == "__main__":
    main()
