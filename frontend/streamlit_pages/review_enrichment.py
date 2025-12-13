"""
Review enrichment page
"""
import streamlit as st
import pandas as pd
from api_client import get_enrichment, enrich_leads, get_merged_results

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
    # Initialize review enriched results session state (separate from test enriched results)
    if "review_enriched_results" not in st.session_state:
        st.session_state.review_enriched_results = {}
    
    selected_project = st.session_state.selected_project
    selected_enrichment = st.session_state.selected_enrichment
    
    if not selected_project or not selected_enrichment:
        return
    
    project_id = selected_project['id']
    enrichment_id = selected_enrichment['id']
    enrichment_name = selected_enrichment.get("enrichment_name", "")
    result_format = selected_enrichment.get("result_format", "")
    
    if st.button("🚀 Run Enrichment on All Leads", width='stretch'):
        if not enrichment_name:
            st.warning("⚠️ Enrichment name is required to run enrichment.")
            return
        if not result_format:
            st.warning("⚠️ Result format must be set before running enrichment.")
            return
        
        with st.spinner("🔄 Running enrichment on all leads (this may take several minutes)..."):
            try:
                # Get all leads from merged results
                merged_results = get_merged_results(project_id)
                if not merged_results or not merged_results.get("data"):
                    st.warning("⚠️ No leads available for this project.")
                    return
                
                leads_data = merged_results["data"]
                # Filter to only include lead column
                filtered_leads = []
                for row in leads_data:
                    filtered_row = {"lead": row.get("lead", "")}
                    filtered_leads.append(filtered_row)
                
                result = enrich_leads(project_id, enrichment_id, filtered_leads, enrichment_name, result_format)
                if result and result.get('success'):
                    # Store enriched results in review-specific session state, keyed by project_id and enrichment_id
                    results_key = f"{project_id}_{enrichment_id}"
                    st.session_state.review_enriched_results[results_key] = {
                        "data": result.get("enriched_leads", filtered_leads),
                        "columns": result.get("columns", ["lead"]),
                        "count": result.get("leads_processed", len(filtered_leads)),
                        "enrichment_name": enrichment_name,
                        "result_format": result_format
                    }
                    st.success(f"✅ Enrichment '{enrichment_name}' completed successfully on {result.get('leads_processed', len(filtered_leads))} lead(s).")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to run enrichment: {result.get('message', 'Unknown error') if result else 'No response from server'}")
            except Exception as e:
                st.error(f"❌ Error running enrichment: {str(e)}")
    
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
        enrichment_name = enriched_results.get("enrichment_name", "")
        result_format = enriched_results.get("result_format", "")
        if result_format == "True/False" and enrichment_name in display_df.columns:
            display_df[enrichment_name] = display_df[enrichment_name].apply(lambda x: "True" if x is True else "False" if x is False else str(x))
        
        st.dataframe(display_df, width='stretch', hide_index=True)
        st.caption(f"Showing {len(display_df)} enriched lead(s) with '{enriched_results.get('enrichment_name', '')}' column.")