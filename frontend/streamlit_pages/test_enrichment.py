"""
Test enrichment page - edit enrichment configuration
"""
import streamlit as st
from api import get_enrichment, update_enrichment, get_merged_results, test_enrich_leads
from utils.display_errors import call_api
import pandas as pd


def show_test_enrichment():
    """Test enrichment page - edit enrichment configuration"""
    selected_project = st.session_state.selected_project
    selected_enrichment = st.session_state.selected_enrichment

    if not selected_project:
        st.error("No project selected")
        return
    
    if selected_enrichment:
        enrichment = call_api(get_enrichment, selected_enrichment['id'])
        if enrichment:
            st.session_state.selected_enrichment = enrichment
        else:
            enrichment = selected_enrichment
    else:
        st.error("No enrichment selected")
        return

    init_test_enrichment_session_state()
    
    # Initialize session state values from database ONLY if they don't exist
    # This allows user edits to persist across reruns
    enrichment_id = enrichment['id']
    format_key = f"enrichment_result_format_edit_{enrichment_id}"
    true_if_key = f"{format_key}_true_if"
    false_if_key = f"{format_key}_false_if"
    number_def_key = f"{format_key}_number_def"
    text_def_key = f"{format_key}_text_def"
    
    # Only initialize if not already set (don't overwrite user edits)
    if format_key not in st.session_state:
        st.session_state[format_key] = enrichment.get('result_format', '')
    if true_if_key not in st.session_state:
        st.session_state[true_if_key] = enrichment.get('result_true_if', '')
    if false_if_key not in st.session_state:
        st.session_state[false_if_key] = enrichment.get('result_false_if', '')
    if number_def_key not in st.session_state:
        st.session_state[number_def_key] = enrichment.get('result_number_value', '')
    if text_def_key not in st.session_state:
        st.session_state[text_def_key] = enrichment.get('result_text_value', '')

    project_id = selected_project['id']
    enrichment_id = enrichment['id']

    st.title(f"🧪 Test Enrichment - {enrichment['enrichment_name']}")
    st.info("Edit the enrichment configuration below. Saved changes will be reflected in the Review Enrichment page.")
    show_review_enrichment_page()
    
    st.divider()

    show_leads()
    st.divider()
    
    st.subheader("🧪 Edit Enrichment Configuration")
    st.markdown("Configure how the enrichment agent extracts information from each lead.")
    
    # Column name editor (full width at top)
    show_column_name_editor(enrichment)
    st.markdown("")  # Add spacing
    
    # Use columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        show_goal_editor(enrichment)
        st.markdown("")  # Add spacing
    
    with col2:
        show_acceptable_evidence_editor(enrichment)
        st.markdown("")  # Add spacing
    
    # Result format section (full width)
    show_result_format_editor(enrichment)
    
    # Check if any changes were made and show save button
    has_changes = check_enrichment_changes(enrichment)
    save_changes_key = f"save_all_changes_message_{enrichment_id}"
    
    # Clear save message if new changes are detected
    if has_changes and st.session_state.get(save_changes_key):
        st.session_state[save_changes_key] = None
    
    # Display save message below the button if it exists (from previous save)
    # Only show if there are no pending changes (to avoid confusion)
    if st.session_state.get(save_changes_key) and not has_changes:
        st.success(st.session_state[save_changes_key])
    
    if has_changes:
        if st.button("💾 Save All Changes", key=f"save_all_changes_{enrichment_id}", type="primary", width='stretch'):
            save_all_enrichment_changes(enrichment)
    
    st.divider()
    show_run_enrichment(enrichment)

def show_review_enrichment_page():
    """Button to navigate back to the review enrichment page"""
    if st.button("📋 Back to Review Enrichment", width='stretch'):
        st.session_state.current_page = "review_enrichment"
        st.rerun()

def init_test_enrichment_session_state():
    """Initialize session state for test enrichment page."""
    current_project_id = st.session_state.selected_project.get("id") if st.session_state.selected_project else None
    current_enrichment_id = st.session_state.selected_enrichment.get("id") if st.session_state.selected_enrichment else None
    if "test_enrichment_leads" not in st.session_state:
        st.session_state.test_enrichment_leads = {}
    if current_project_id and current_project_id not in st.session_state.test_enrichment_leads:
        st.session_state.test_enrichment_leads[current_project_id] = {"data": None, "columns": None, "count": 0}
    if "test_enriched_results" not in st.session_state:
        st.session_state.test_enriched_results = {}
    
    # Initialize success message keys
    if current_project_id:
        save_leads_key = f"save_test_leads_message_{current_project_id}"
        if save_leads_key not in st.session_state:
            st.session_state[save_leads_key] = None
    if current_enrichment_id:
        save_changes_key = f"save_all_changes_message_{current_enrichment_id}"
        if save_changes_key not in st.session_state:
            st.session_state[save_changes_key] = None
        run_enrichment_key = f"run_enrichment_message_{current_enrichment_id}"
        if run_enrichment_key not in st.session_state:
            st.session_state[run_enrichment_key] = None


def show_leads():
    """Show first 5 leads for the current project (cached in session state)."""
    project = st.session_state.selected_project
    if not project:
        return
    project_id = project["id"]

    init_test_enrichment_session_state()

    st.subheader("📋 Test Leads")
    st.markdown("Edit or add test leads to validate your enrichment configuration.")

    leads_cache = st.session_state.test_enrichment_leads.get(project_id, {"data": None, "columns": None, "count": 0})

    if leads_cache["data"] is None:
        result = call_api(get_merged_results, project_id)
        if result and result.get("data"):
            leads_data = result["data"][:5]  # first 5 rows
            # Filter to only include lead column
            filtered_data = []
            for row in leads_data:
                filtered_row = {"lead": row.get("lead", "")}
                filtered_data.append(filtered_row)
            st.session_state.test_enrichment_leads[project_id] = {
                "data": filtered_data,
                "columns": ["lead"],
                "count": result.get("count", len(filtered_data)),
            }
            leads_cache = st.session_state.test_enrichment_leads[project_id]

    df = pd.DataFrame(leads_cache["data"] or [])
    # Show lead column and any enrichment columns, exclude id, project_id, and serp_count
    exclude_columns = ["id", "project_id", "serp_count"]
    display_columns = [c for c in df.columns if c not in exclude_columns]
    display_df = df[display_columns] if display_columns else df

    editor_key = f"test_enrichment_leads_editor_{project_id}"
    edited_df = st.data_editor(
        display_df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        key=editor_key,
    )

    # Check if there are changes by comparing the lead values as simple lists
    # Since it's just one column, we can extract the lead values and compare lists
    original_leads = display_df["lead"].tolist() if "lead" in display_df.columns else []
    edited_leads = edited_df["lead"].tolist() if "lead" in edited_df.columns else []
    
    # Compare the lists - catches value changes, additions, deletions
    has_changes = original_leads != edited_leads
    
    save_leads_key = f"save_test_leads_message_{project_id}"
    
    # Clear save message if new changes are detected
    if has_changes and st.session_state.get(save_leads_key):
        st.session_state[save_leads_key] = None
    
    # Display save message below the button if it exists (from previous save)
    # Only show if there are no pending changes (to avoid confusion)
    if st.session_state.get(save_leads_key) and not has_changes:
        st.success(st.session_state[save_leads_key])

    if has_changes:
        if st.button("💾 Save Test Leads", key=f"save_test_leads_{project_id}", width='stretch'):
            st.session_state.test_enrichment_leads[project_id] = {
                "data": edited_df.to_dict(orient="records"),
                "columns": list(edited_df.columns),
                "count": len(edited_df),
            }
            # Store message in session state so it persists across rerun
            st.session_state[save_leads_key] = "✅ Test leads saved successfully."
            st.rerun()

    total_session_leads = len(display_df)

def show_run_enrichment(enrichment):
    """Run enrichment on test leads."""
    project = st.session_state.selected_project
    if not project:
        return
    project_id = project["id"]
    enrichment_id = enrichment["id"]
    # Use session state column_name if it exists (user may have edited it), otherwise use enrichment's saved column_name
    # Column name is REQUIRED before running enrichment
    column_name_key = f"enrichment_column_name_edit_{enrichment_id}"
    column_name = st.session_state.get(column_name_key, '').strip() or enrichment.get("column_name", "") or ""
    result_format = enrichment.get("result_format", "")
    leads_cache = st.session_state.test_enrichment_leads.get(project_id, {"data": []})

    st.subheader("🚀 Run Enrichment on Test Leads")
    st.markdown("Test your configuration by running enrichment on the test leads above.")
    run_enrichment_key = f"run_enrichment_message_{enrichment_id}"
    
    if st.button("Run Enrichment", key=f"run_enrichment_{enrichment_id}", width='stretch'):
        with st.spinner("Running enrichment on test leads..."):
            leads_data = leads_cache.get("data") or []  # Ensure it's always a list, not None
            result = call_api(test_enrich_leads, project_id, enrichment_id, leads_data)
            if result and result.get("success"):
                # Store enriched results in test-specific session state, keyed by project_id and enrichment_id
                results_key = f"{project_id}_{enrichment_id}"
                enrichment_name = enrichment.get("enrichment_name", "")
                st.session_state.test_enriched_results[results_key] = {
                    "data": result.get("enriched_leads", leads_data),
                    "columns": result.get("columns", leads_cache.get("columns", ["lead"])),
                    "count": result.get("leads_processed", len(leads_data)),
                    "enrichment_name": enrichment_name,
                    "column_name": column_name,  # Store the column_name that was used at runtime
                    "result_format": result_format
                }
                
                leads_processed = result.get("leads_processed", len(leads_data))
                # Store message in session state so it persists across rerun
                st.session_state[run_enrichment_key] = f"✅ Enrichment '{enrichment_name}' completed successfully on {leads_processed} test lead(s)."
                st.rerun()
    
    # Display success message below the button if it exists
    if st.session_state.get(run_enrichment_key):
        st.success(st.session_state[run_enrichment_key])
    
    # Display enriched results if available for this specific enrichment
    results_key = f"{project_id}_{enrichment_id}"
    enriched_results = st.session_state.test_enriched_results.get(results_key)
    if enriched_results and enriched_results.get("data"):        
        df = pd.DataFrame(enriched_results["data"])
        
        # Use the column_name that was used when the enrichment was run (stored in results)
        # This ensures we display the correct columns even if the user has since edited the column_name
        result_column_name = enriched_results.get("column_name", enrichment.get("column_name", ""))
        
        # Only show: lead, column_name, column_name_reasoning, column_name_evidence
        display_columns = ["lead"]
        if result_column_name in df.columns:
            display_columns.append(result_column_name)
        reasoning_col = f"{result_column_name}_reasoning"
        evidence_col = f"{result_column_name}_evidence"
        if reasoning_col in df.columns:
            display_columns.append(reasoning_col)
        if evidence_col in df.columns:
            display_columns.append(evidence_col)
        
        # Filter to only show these columns
        display_df = df[display_columns] if display_columns else df
        
        # Convert boolean values to strings for True/False format
        if result_format == "True/False" and result_column_name in display_df.columns:
            display_df[result_column_name] = display_df[result_column_name].apply(lambda x: "True" if x is True else "False" if x is False else str(x))
        
        st.dataframe(display_df, width='stretch', hide_index=True)

def show_column_name_editor(enrichment):
    """Editable column name field - REQUIRED before running enrichment"""
    st.markdown("**📝 Column Name***")
    enrichment_id = enrichment['id']
    column_name_key = f"enrichment_column_name_edit_{enrichment_id}"
    if column_name_key not in st.session_state:
        st.session_state[column_name_key] = enrichment.get('column_name', '') or ''
    
    st.text_input(
        "Column Name",
        key=column_name_key,
        placeholder="e.g. more_than_1_doctor",
        label_visibility="collapsed",
        help="Database column name used in the prompt (lowercase, underscores only). REQUIRED before running enrichment. Changing this affects how the AI agent structures its output.",
    )

def show_goal_editor(enrichment):
    """Editable goal field"""
    st.markdown("**🎯 Goal***")
    goal_key = f"enrichment_goal_edit_{enrichment['id']}"
    if goal_key not in st.session_state:
        st.session_state[goal_key] = enrichment.get('goal', '')

    st.text_area(
        "Goal",
        key=goal_key,
        placeholder="e.g., Determine if this medical center has more than 1 doctor",
        height=50,
        label_visibility="collapsed",
        help="Describe what this enrichment is trying to achieve",
    )

def show_acceptable_evidence_editor(enrichment):
    """Editable agent reasoning field"""
    st.markdown("**🤖 Agent Reasoning***")
    evidence_key = f"enrichment_acceptable_evidence_edit_{enrichment['id']}"
    if evidence_key not in st.session_state:
        st.session_state[evidence_key] = enrichment.get('acceptable_evidence', '')

    st.text_area(
        "Agent Reasoning",
        key=evidence_key,
        placeholder="e.g., Look for staff listings, about pages, or directory information. Determine if there are more than 1 doctor listed.",
        height=50,
        label_visibility="collapsed",
        help="Provide context and reasoning guidelines for how the agent should approach this enrichment",
    )

def show_result_format_editor(enrichment):
    """Editable result format field"""
    st.markdown("**📝 Result Format***")
    format_key = f"enrichment_result_format_edit_{enrichment['id']}"
    true_if_key = f"{format_key}_true_if"
    false_if_key = f"{format_key}_false_if"
    number_def_key = f"{format_key}_number_def"
    text_def_key = f"{format_key}_text_def"
    
    # Initialize all session state values from enrichment if not already set
    if format_key not in st.session_state:
        current_format = enrichment.get('result_format', '')
        st.session_state[format_key] = current_format if current_format else ""
    if true_if_key not in st.session_state:
        st.session_state[true_if_key] = enrichment.get('result_true_if', '')
    if false_if_key not in st.session_state:
        st.session_state[false_if_key] = enrichment.get('result_false_if', '')
    if number_def_key not in st.session_state:
        st.session_state[number_def_key] = enrichment.get('result_number_value', '')
    if text_def_key not in st.session_state:
        st.session_state[text_def_key] = enrichment.get('result_text_value', '')

    # Build options
    options = ["", "True/False", "Text", "Number"]
    
    # Ensure session state value is valid (only check/reset if it's truly invalid)
    # Don't reset if user just selected a valid option
    current_format_value = st.session_state.get(format_key, "")
    if current_format_value and current_format_value not in options:
        # Only reset if it's an invalid value (not empty and not in options)
        st.session_state[format_key] = ""
    
    # Create selectbox - uses key parameter so Streamlit automatically uses session state value
    # and updates it when user selects a new value
    st.selectbox(
        "Result Format",
        options=options,
        key=format_key,
        label_visibility="collapsed",
        help="Select the expected format for the enrichment result",
    )
    
    # Get the selected format from session state
    selected_format = st.session_state.get(format_key, "")

    if selected_format == "True/False":
        st.text_input(
            "True if*",
            key=true_if_key,
            placeholder="e.g., The company has more than 1 doctor working there",
        )
        st.text_input(
            "False if*",
            key=false_if_key,
            placeholder="e.g., The company has only 1 doctor or no doctors listed",
        )
    elif selected_format == "Number":
        st.text_input(
            "Define the Number Output*",
            key=number_def_key,
            placeholder="e.g., Determine if there are more than 1 doctor. Return true if yes, false if no.",
        )
    elif selected_format == "Text":
        st.text_input(
            "Define the Text Output*",
            key=text_def_key,
            placeholder="e.g., The company's primary service area or specialty",
        )


def check_enrichment_changes(enrichment):
    """Check if any enrichment configuration fields have been changed"""
    enrichment_id = enrichment['id']
    
    # Get all session state keys for this enrichment
    column_name_key = f"enrichment_column_name_edit_{enrichment_id}"
    goal_key = f"enrichment_goal_edit_{enrichment_id}"
    evidence_key = f"enrichment_acceptable_evidence_edit_{enrichment_id}"
    format_key = f"enrichment_result_format_edit_{enrichment_id}"
    true_if_key = f"{format_key}_true_if"
    false_if_key = f"{format_key}_false_if"
    number_def_key = f"{format_key}_number_def"
    text_def_key = f"{format_key}_text_def"
    
    # Compare current session state values with original enrichment values
    column_name_changed = st.session_state.get(column_name_key, '') != enrichment.get('column_name', '')
    goal_changed = st.session_state.get(goal_key, '') != enrichment.get('goal', '')
    evidence_changed = st.session_state.get(evidence_key, '') != enrichment.get('acceptable_evidence', '')
    format_changed = st.session_state.get(format_key, '') != enrichment.get('result_format', '')
    true_if_changed = st.session_state.get(true_if_key, '') != enrichment.get('result_true_if', '')
    false_if_changed = st.session_state.get(false_if_key, '') != enrichment.get('result_false_if', '')
    number_changed = st.session_state.get(number_def_key, '') != enrichment.get('result_number_value', '')
    text_changed = st.session_state.get(text_def_key, '') != enrichment.get('result_text_value', '')
    
    return column_name_changed or goal_changed or evidence_changed or format_changed or true_if_changed or false_if_changed or number_changed or text_changed

def save_all_enrichment_changes(enrichment):
    """Save all enrichment configuration changes at once"""
    enrichment_id = enrichment['id']
    
    # Get all session state keys for this enrichment
    column_name_key = f"enrichment_column_name_edit_{enrichment_id}"
    goal_key = f"enrichment_goal_edit_{enrichment_id}"
    evidence_key = f"enrichment_acceptable_evidence_edit_{enrichment_id}"
    format_key = f"enrichment_result_format_edit_{enrichment_id}"
    true_if_key = f"{format_key}_true_if"
    false_if_key = f"{format_key}_false_if"
    number_def_key = f"{format_key}_number_def"
    text_def_key = f"{format_key}_text_def"
    
    # Get values from session state - backend will validate
    column_name = (st.session_state.get(column_name_key, '') or '').strip()
    
    # Build payload with all current values - handle None values from session state
    payload = {
        "column_name": column_name,
        "goal": st.session_state.get(goal_key, '') or '',
        "acceptable_evidence": st.session_state.get(evidence_key, '') or '',
        "result_format": st.session_state.get(format_key, '') or '',
    }
    
    # Add format-specific fields based on selected format
    selected_format = st.session_state.get(format_key, '') or ''
    if selected_format == "True/False":
        payload["result_true_if"] = st.session_state.get(true_if_key, '') or ''
        payload["result_false_if"] = st.session_state.get(false_if_key, '') or ''
        payload["result_number_value"] = ""
        payload["result_text_value"] = ""
    elif selected_format == "Number":
        payload["result_number_value"] = st.session_state.get(number_def_key, '') or ''
        payload["result_true_if"] = ""
        payload["result_false_if"] = ""
        payload["result_text_value"] = ""
    elif selected_format == "Text":
        payload["result_text_value"] = st.session_state.get(text_def_key, '') or ''
        payload["result_true_if"] = ""
        payload["result_false_if"] = ""
        payload["result_number_value"] = ""
    else:
        # If no format selected, clear all format-specific fields
        payload["result_true_if"] = ""
        payload["result_false_if"] = ""
        payload["result_number_value"] = ""
        payload["result_text_value"] = ""
    
    # Save all changes
    with st.spinner("💾 Saving all changes..."):
        result = call_api(update_enrichment, enrichment_id, **payload)
        if result:
            # Show immediate success message
            st.success("✅ All changes saved successfully!")
            # Also store message in session state so it persists across rerun
            save_changes_key = f"save_all_changes_message_{enrichment_id}"
            st.session_state[save_changes_key] = "✅ All changes saved successfully!"
            updated = call_api(get_enrichment, enrichment_id)
            if updated:
                st.session_state.selected_enrichment = updated
            st.rerun()