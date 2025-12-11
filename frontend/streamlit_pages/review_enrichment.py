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

    st.title(f"📋 Run Enrichment - {enrichment['enrichment_name']}")
    
    # Navigation note + button
    st.info("This page is read-only. To change these fields, go to the Enrichment Test page.")
    show_test_enrichment_page()
    st.divider()
    
    # Display enrichment configuration (read-only)
    st.subheader("📋 Review Enrichment Configuration")
    show_goal(enrichment)
    show_acceptable_evidence(enrichment)
    show_result_format(enrichment)
    
    # Action button
    show_run_on_all_leads()

def show_test_enrichment_page():
    """Button to navigate to test enrichment page"""
    if st.button("🔄 Go To Enrichment Test Page", width='stretch'):
        st.session_state.current_page = "test_enrichment"
        st.rerun()

def show_goal(enrichment):
    """Display enrichment goal (read-only)"""
    st.write("**🎯 Goal:**")
    goal_text = enrichment.get('goal', 'Not set')
    st.text_area(
        "Goal",
        value=goal_text,
        height=100,
        disabled=True,
        label_visibility="collapsed"
    )

def show_acceptable_evidence(enrichment):
    """Display acceptable evidence (read-only)"""
    st.write("**📝 Acceptable Evidence:**")
    evidence_text = enrichment.get('acceptable_evidence', 'Not set')
    st.text_area(
        "Acceptable Evidence",
        value=evidence_text,
        height=100,
        disabled=True,
        label_visibility="collapsed"
    )

def show_result_format(enrichment):
    """Display result format (read-only)"""
    st.write("**📝 Result Format:**")
    result_format = enrichment.get('result_format', 'Not set')
    options = ["", "True/False", "Text", "Number"]
    current_index = 0
    if result_format in options:
        current_index = options.index(result_format)
    elif result_format != 'Not set':
        options = [result_format] + options
        current_index = 0

    st.selectbox(
        "Result Format",
        options=options,
        index=current_index,
        disabled=True,
        label_visibility="collapsed"
    )

    # Display conditional fields
    if result_format == "True/False":
        st.text_input(
            "True if",
            value=enrichment.get("result_true_if", "Not set"),
            disabled=True,
            placeholder="Not set"
        )
        st.text_input(
            "False if",
            value=enrichment.get("result_false_if", "Not set"),
            disabled=True,
            placeholder="Not set"
        )
    elif result_format == "Number":
        st.text_input(
            "Define the Value",
            value=enrichment.get("result_number_value", "Not set"),
            disabled=True,
            placeholder="Not set"
        )
    elif result_format == "Text":
        st.text_input(
            "What do you want returned",
            value=enrichment.get("result_text_value", "Not set"),
            disabled=True,
            placeholder="Not set"
        )

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