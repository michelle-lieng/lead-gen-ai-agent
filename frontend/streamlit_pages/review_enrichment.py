"""
Review enrichment page
"""

import streamlit as st
import pandas as pd
from api import get_enrichment, enrich_leads, get_merged_results, get_job_status
from api.base import ApiError
from utils.ui_errors import show_api_error
from utils.display_errors import call_api

import time


def show_review_enrichment():
    """Review enrichment page"""
    selected_enrichment = st.session_state.selected_enrichment

    if selected_enrichment:
        enrichment = call_api(get_enrichment, selected_enrichment["id"])
        if enrichment:
            st.session_state.selected_enrichment = enrichment
        else:
            enrichment = selected_enrichment
    else:
        st.error("No enrichment selected")
        return

    st.title(f"📋 Run Enrichment - {enrichment['enrichment_name']}")

    # Navigation note + button
    st.info(
        "This page is read-only. To change these fields, go to the Enrichment Test page."
    )
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
    if st.button("🔄 Go To Enrichment Test Page", width="stretch"):
        st.session_state.current_page = "test_enrichment"
        st.rerun()


def show_column_name(enrichment):
    """Display column name (read-only)"""
    st.write("**📝 Column Name:**")
    column_name_text = enrichment.get("column_name", "Not set")
    st.text_input(
        "Column Name",
        value=column_name_text,
        disabled=True,
        label_visibility="collapsed",
    )


def show_goal(enrichment):
    """Display enrichment goal (read-only)"""
    st.write("**🎯 Goal:**")
    goal_text = enrichment.get("goal", "Not set")
    st.text_area(
        "Goal", value=goal_text, height=50, disabled=True, label_visibility="collapsed"
    )


def show_acceptable_evidence(enrichment):
    """Display agent reasoning (read-only)"""
    st.write("**🤖 Agent Reasoning:**")
    evidence_text = enrichment.get("acceptable_evidence", "Not set")
    st.text_area(
        "Agent Reasoning",
        value=evidence_text,
        height=50,
        disabled=True,
        label_visibility="collapsed",
    )


def show_result_format(enrichment):
    """Display result format (read-only)"""
    st.write("**📝 Result Format:**")
    result_format = enrichment.get("result_format", "Not set")
    options = ["", "True/False", "Text", "Number"]
    current_index = 0
    if result_format in options:
        current_index = options.index(result_format)
    elif result_format != "Not set":
        options = [result_format] + options
        current_index = 0

    st.selectbox(
        "Result Format",
        options=options,
        index=current_index,
        disabled=True,
        label_visibility="collapsed",
    )

    # Display conditional fields
    if result_format == "True/False":
        st.text_input(
            "True if",
            value=enrichment.get("result_true_if", "Not set"),
            disabled=True,
            placeholder="Not set",
        )
        st.text_input(
            "False if",
            value=enrichment.get("result_false_if", "Not set"),
            disabled=True,
            placeholder="Not set",
        )
    elif result_format == "Number":
        st.text_input(
            "Define the Value",
            value=enrichment.get("result_number_value", "Not set"),
            disabled=True,
            placeholder="Not set",
        )
    elif result_format == "Text":
        st.text_input(
            "What do you want returned",
            value=enrichment.get("result_text_value", "Not set"),
            disabled=True,
            placeholder="Not set",
        )


def show_run_on_all_leads():
    """Button to run enrichment on all leads"""
    # Initialize review enriched results session state (separate from test enriched results)
    if "review_enriched_results" not in st.session_state:
        st.session_state.review_enriched_results = {}

    selected_project = st.session_state.selected_project
    selected_enrichment = st.session_state.selected_enrichment

    if not selected_project or not selected_enrichment:
        return

    project_id = selected_project["id"]
    enrichment_id = selected_enrichment["id"]
    column_name = selected_enrichment.get("column_name", "")
    result_format = selected_enrichment.get("result_format", "")

    job_status = call_api(get_job_status, project_id, "enrichments", enrichment_id)

    is_job_running = job_status and job_status.get("status") == "running"

    if is_job_running:
        with st.spinner(
            "🔄 Running enrichment on all leads (this may take several minutes)..."
        ):
            # Auto-refresh every 3 seconds while job is running
            time.sleep(3)
            st.rerun()

    # Handle completed job
    if job_status and job_status.get("status") == "completed":
        # Job completed - fetch and display results
        # Clear any previous error messages
        error_key = f"enrichment_error_{project_id}_{enrichment_id}"
        if error_key in st.session_state:
            del st.session_state[error_key]
        
        # Fetch merged results to show updated data
        merged_results = call_api(get_merged_results, project_id)
        if merged_results and merged_results.get("data"):
            results_key = f"{project_id}_{enrichment_id}"
            enrichment_name = selected_enrichment.get("enrichment_name", "")
            st.session_state.review_enriched_results[results_key] = {
                "data": merged_results["data"],
                "columns": merged_results.get("columns", ["lead"]),
                "count": merged_results.get("count", len(merged_results["data"])),
                "enrichment_name": enrichment_name,
                "column_name": column_name,
                "result_format": result_format,
            }
            # Clear job status to prevent re-triggering
            # We'll mark it as handled by storing a flag
            handled_key = f"job_handled_{project_id}_{enrichment_id}"
            if not st.session_state.get(handled_key):
                st.success(
                    f"✅ Enrichment '{enrichment_name}' completed successfully! Results have been automatically saved to merged leads."
                )
                st.session_state[handled_key] = True
                st.rerun()
    
    # Handle failed job
    if job_status and job_status.get("status") == "failed":
        error_message = job_status.get("error_message", "Unknown error occurred")
        error_key = f"enrichment_error_{project_id}_{enrichment_id}"
        if not st.session_state.get(error_key):
            st.error(f"❌ Enrichment failed: {error_message}")
            st.session_state[error_key] = True
            # Clear handled flag so user can try again
            handled_key = f"job_handled_{project_id}_{enrichment_id}"
            if handled_key in st.session_state:
                del st.session_state[handled_key]

    # Show button only if job is not running
    if not is_job_running:
        if st.button("🚀 Run Enrichment on All Leads", width="stretch"):
            # Clear any previous error/handled flags
            error_key = f"enrichment_error_{project_id}_{enrichment_id}"
            handled_key = f"job_handled_{project_id}_{enrichment_id}"
            if error_key in st.session_state:
                del st.session_state[error_key]
            if handled_key in st.session_state:
                del st.session_state[handled_key]
            
            with st.spinner(
                "🔄 Running enrichment on all leads (this may take several minutes)..."
            ):
                # Get all leads from merged results
                merged_results = call_api(get_merged_results, project_id)
                if not merged_results or not merged_results.get("data"):
                    st.warning("⚠️ No leads available for this project.")
                    return

                leads_data = merged_results["data"]
                # Try to call enrich_leads, catch JOB_ALREADY_RUNNING error specifically
                try:
                    result = enrich_leads(project_id, enrichment_id, leads_data)
                    if result:
                        # Store enriched results in review-specific session state, keyed by project_id and enrichment_id
                        results_key = f"{project_id}_{enrichment_id}"
                        enrichment_name = selected_enrichment.get("enrichment_name", "")
                        st.session_state.review_enriched_results[results_key] = {
                            "data": result.get("enriched_leads"),
                            "columns": result.get("columns", ["lead"]),
                            "count": result.get("leads_processed"),
                            "enrichment_name": enrichment_name,
                            "column_name": column_name,
                            "result_format": result_format,
                        }
                        st.success(
                            f"✅ Enrichment '{enrichment_name}' completed successfully on {result.get('leads_processed')} lead(s). Results have been automatically saved to merged leads."
                        )
                        st.rerun()
                except ApiError as e:
                    # Check if it's the "job already running" error
                    if e.code == "JOB_ALREADY_RUNNING":
                        # Job is already running - trigger polling
                        st.info("🔄 Enrichment is already running. Checking status...")
                        st.rerun()
                    else:
                        # For other errors, use the standard error handler
                        show_api_error(e)

    # Display enriched results if available for this specific enrichment
    results_key = f"{project_id}_{enrichment_id}"
    enriched_results = st.session_state.review_enriched_results.get(results_key)
    if enriched_results and enriched_results.get("data"):
        st.write("**📊 Enriched Results:**")
        df = pd.DataFrame(enriched_results["data"])
        # Exclude id, project_id, and serp_count columns
        exclude_columns = ["id", "project_id", "serp_count"]
        display_columns = [c for c in df.columns if c not in exclude_columns]
        display_df = df[display_columns] if display_columns else df

        # Convert boolean values to strings for True/False format
        column_name = enriched_results.get("column_name", "")
        result_format = enriched_results.get("result_format", "")
        if result_format == "True/False" and column_name in display_df.columns:
            display_df[column_name] = display_df[column_name].apply(
                lambda x: "True" if x is True else "False" if x is False else str(x)
            )

        st.dataframe(display_df, width="stretch", hide_index=True)
        st.caption(
            f"Showing {len(display_df)} enriched lead(s) with '{enriched_results.get('enrichment_name', '')}' column."
        )
