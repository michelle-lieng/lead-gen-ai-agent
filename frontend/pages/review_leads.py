"""
Review leads page
"""
import streamlit as st

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
