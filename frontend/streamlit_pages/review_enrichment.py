"""
Review enrichment page
"""
import streamlit as st
import pandas as pd
from api import get_enrichment, enrich_leads, get_merged_results
from utils.display_errors import call_api

def show_review_enrichment():
    """Review enrichment page"""
    selected_project = st.session_state.selected_project
    project_id = selected_project['id']
    selected_enrichment = st.session_state.selected_enrichment

    if selected_enrichment:
        enrichment = call_api(get_enrichment, selected_enrichment['id'])
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
    show_column_name(enrichment)
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

def show_column_name(enrichment):
    """Display column name (read-only)"""
    st.write("**📝 Column Name:**")
    column_name_text = enrichment.get('column_name', 'Not set')
    st.text_input(
        "Column Name",
        value=column_name_text,
        disabled=True,
        label_visibility="collapsed"
    )

def show_goal(enrichment):
    """Display enrichment goal (read-only)"""
    st.write("**🎯 Goal:**")
    goal_text = enrichment.get('goal', 'Not set')
    st.text_area(
        "Goal",
        value=goal_text,
        height=50,
        disabled=True,
        label_visibility="collapsed"
    )

def show_acceptable_evidence(enrichment):
    """Display agent reasoning (read-only)"""
    st.write("**🤖 Agent Reasoning:**")
    evidence_text = enrichment.get('acceptable_evidence', 'Not set')
    st.text_area(
        "Agent Reasoning",
        value=evidence_text,
        height=50,
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

def validate_enrichment_config(enrichment):
    """Validate that all required enrichment configuration fields are set"""
    errors = []
    
    # Helper function to safely get and strip a value
    def get_stripped_value(key, default=""):
        value = enrichment.get(key)
        if value is None:
            return default
        return str(value).strip() if value else default
    
    # Core required fields
    column_name = get_stripped_value("column_name")
    if not column_name:
        errors.append("Column Name")
    
    goal = get_stripped_value("goal")
    if not goal:
        errors.append("Goal")
    
    acceptable_evidence = get_stripped_value("acceptable_evidence")
    if not acceptable_evidence:
        errors.append("Agent Reasoning")
    
    result_format = get_stripped_value("result_format")
    if not result_format:
        errors.append("Result Format")
    
    # Format-specific fields
    if result_format == "True/False":
        result_true_if = get_stripped_value("result_true_if")
        if not result_true_if:
            errors.append("True if")
        result_false_if = get_stripped_value("result_false_if")
        if not result_false_if:
            errors.append("False if")
    elif result_format == "Number":
        result_number_value = get_stripped_value("result_number_value")
        if not result_number_value:
            errors.append("Define the Value")
    elif result_format == "Text":
        result_text_value = get_stripped_value("result_text_value")
        if not result_text_value:
            errors.append("What do you want returned")
    
    return errors

def show_run_on_all_leads():
    """Button to run enrichment on all leads"""
    # Initialize review enriched results session state (separate from test enriched results)
    if "review_enriched_results" not in st.session_state:
        st.session_state.review_enriched_results = {}
    
    # Initialize enrichment running state
    if "review_enrichment_running" not in st.session_state:
        st.session_state.review_enrichment_running = False
    
    selected_project = st.session_state.selected_project
    selected_enrichment = st.session_state.selected_enrichment
    
    if not selected_project or not selected_enrichment:
        return
    
    project_id = selected_project['id']
    enrichment_id = selected_enrichment['id']
    column_name = selected_enrichment.get("column_name", "")
    result_format = selected_enrichment.get("result_format", "")
    
    # Show warning message if enrichment is running
    if st.session_state.review_enrichment_running:
        st.warning("⚠️ Please do not navigate away from this page (in-app) as progress will be lost.")
    
    if st.button("🚀 Run Enrichment on All Leads", width='stretch', disabled=st.session_state.review_enrichment_running):        
        # Clear previous messages when starting new enrichment
        if "review_enrichment_success" in st.session_state:
            st.session_state.pop("review_enrichment_success", None)
        if "review_enrichment_error" in st.session_state:
            st.session_state.pop("review_enrichment_error", None)
        
        # Validate configuration before running
        validation_errors = validate_enrichment_config(selected_enrichment)
        if validation_errors:
            error_message = "❌ Please complete the following required fields before running enrichment:\n- " + "\n- ".join(validation_errors)
            st.error(error_message)
        else:
            st.session_state.review_enrichment_running = True
            st.rerun()
    
    # Run enrichment if flag is set
    if st.session_state.review_enrichment_running:
        with st.spinner("🔄 Running enrichment on all leads (this may take several minutes)..."):
            # Get all leads from merged results
            merged_results = call_api(get_merged_results, project_id)
            if not merged_results or not merged_results.get("data"):
                st.session_state.review_enrichment_error = "❌ No leads to enrich."
                st.session_state.review_enrichment_running = False
                st.rerun()
                return
            
            leads_data = merged_results["data"]
            result = call_api(enrich_leads, project_id, enrichment_id, leads_data)
            # Reset running state regardless of success or failure
            st.session_state.review_enrichment_running = False
            enrichment_name = selected_enrichment.get("enrichment_name", "")
            
            if result:
                enriched_leads = result.get("enriched_leads", [])
                
                if not enriched_leads or len(enriched_leads) == 0:
                    # Empty enriched_leads means all leads were already enriched
                    st.session_state.review_enrichment_success = f"✅ Enrichment '{enrichment_name}' already completed on all leads."
                else:
                    # Store enriched results in review-specific session state, keyed by project_id and enrichment_id
                    results_key = f"{project_id}_{enrichment_id}"
                    st.session_state.review_enriched_results[results_key] = {
                        "data": enriched_leads,
                        "columns": result.get("columns", ["lead"]),
                        "count": result.get("leads_processed"),
                        "enrichment_name": enrichment_name,
                        "column_name": column_name,
                        "result_format": result_format
                    }
                    st.session_state.review_enrichment_success = f"✅ Enrichment '{enrichment_name}' completed successfully on {result.get('leads_processed')} lead(s). Results have been automatically saved to merged leads."
            st.rerun()
    
    # Display success message if it exists in session state
    if "review_enrichment_success" in st.session_state:
        st.success(st.session_state.review_enrichment_success)
        # Clear the success message after displaying it
        st.session_state.pop("review_enrichment_success", None)
    
    # Display error message if it exists in session state
    if "review_enrichment_error" in st.session_state:
        st.error(st.session_state.review_enrichment_error)
        # Clear the error message after displaying it
        st.session_state.pop("review_enrichment_error", None)
    
    # Display enriched results if available for this specific enrichment
    results_key = f"{project_id}_{enrichment_id}"
    enriched_results = st.session_state.review_enriched_results.get(results_key)
    if enriched_results and enriched_results.get("data"):
        st.write("**📊 Enriched Results:**")
        df = pd.DataFrame(enriched_results["data"])
        # Exclude id, project_id, and serp_count columns
        exclude_columns = ["id", "project_id", "serp_count"]
        display_columns = [c for c in df.columns if c not in exclude_columns]
        display_df = df[display_columns].copy() if display_columns else df.copy()
        
        # Convert boolean values to strings for True/False format
        column_name = enriched_results.get("column_name", "")
        result_format = enriched_results.get("result_format", "")
        if result_format == "True/False" and column_name in display_df.columns:
            display_df[column_name] = display_df[column_name].apply(lambda x: "True" if x is True else "False" if x is False else str(x))
        elif result_format == "Number" and column_name in display_df.columns:
            display_df[column_name] = display_df[column_name].apply(lambda x: str(x) if pd.notna(x) else "")
        
        st.dataframe(display_df, width='stretch', hide_index=True)
        st.caption(f"Showing {len(display_df)} enriched lead(s) with '{enriched_results.get('enrichment_name', '')}' column.")