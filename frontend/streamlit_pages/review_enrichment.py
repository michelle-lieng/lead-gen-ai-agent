"""
Review enrichment page
"""
import streamlit as st
import pandas as pd
from api_client import get_enrichment, enrich_leads

def show_review_enrichment():
    """Review enrichment page"""
    selected_project = st.session_state.selected_project
    project_id = selected_project['id']
    selected_enrichment = st.session_state.selected_enrichment

    if selected_enrichment:
        enrichment = get_enrichment(selected_enrichment['id'])
        if enrichment:
            st.session_state.selected_enrichment = enrichment
        else:
            enrichment = selected_enrichment
    else:
        st.error("No enrichment selected")
        return

    st.markdown(f"# 📋 Review Enrichment - {enrichment['enrichment_name']}")
    st.markdown("---")
    
    # Navigation button
    show_test_enrichment_page()
    st.markdown("---")
    
    # Display enrichment configuration (read-only)
    show_goal(enrichment)
    show_acceptable_evidence(enrichment)
    show_result_format(enrichment)
    st.markdown("---")
    
    # Action button
    show_run_on_all_leads()
    st.markdown("---")

def show_test_enrichment_page():
    """Button to navigate to test enrichment page"""
    if st.button("🔄 Go To Enrichment Test Page", width='stretch'):
        st.session_state.current_page = "test_enrichment"
        st.rerun()

def show_goal(enrichment):
    """Display enrichment goal (read-only)"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 🎯 Goal:")
    with col2:
        goal_text = enrichment.get('goal', 'Not set')
        if goal_text:
            st.info(goal_text)
        else:
            st.info("No goal specified")

def show_acceptable_evidence(enrichment):
    """Display acceptable evidence (read-only)"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 📝 Acceptable Evidence:")
    with col2:
        evidence_text = enrichment.get('acceptable_evidence', 'Not set')
        if evidence_text:
            st.info(evidence_text)
        else:
            st.info("No acceptable evidence specified")

def show_result_format(enrichment):
    """Display result format (read-only)"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 📝 Result Format:")
    with col2:
        result_format = enrichment.get('result_format', 'Not set')
        if result_format:
            # Display as a badge-like info box
            st.info(f"**{result_format}**")
        else:
            st.info("No result format specified")

def show_run_on_all_leads():
    """Button to run enrichment on all leads"""
    if st.button("🚀 Run Enrichment on All Leads", width='stretch'):
        selected_project = st.session_state.selected_project
        selected_enrichment = st.session_state.selected_enrichment
        
        if not selected_project:
            st.error("No project selected")
            return
        if not selected_enrichment:
            st.error("No enrichment selected")
            return
        
        project_id = selected_project['id']
        enrichment_id = selected_enrichment['id']
        
        with st.spinner("🔄 Running enrichment on all leads (this may take several minutes)..."):
            try:
                result = enrich_leads(project_id, enrichment_id)
                if result and result.get('success'):
                    st.success(f"✅ Enrichment completed! {result.get('message', '')}")
                else:
                    st.error(f"❌ Failed to run enrichment: {result.get('message', 'Unknown error') if result else 'No response from server'}")
            except Exception as e:
                st.error(f"❌ Error running enrichment: {str(e)}")