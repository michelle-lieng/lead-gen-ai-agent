"""
Test enrichment page - edit enrichment configuration
"""
import streamlit as st
from api_client import get_enrichment, update_enrichment_fields, get_merged_results

def show_test_enrichment():
    """Test enrichment page - edit enrichment configuration"""
    selected_project = st.session_state.selected_project
    selected_enrichment = st.session_state.selected_enrichment

    if not selected_project:
        st.error("No project selected")
        return
    
    if selected_enrichment:
        enrichment = get_enrichment(selected_enrichment['id'])
        if enrichment:
            st.session_state.selected_enrichment = enrichment
        else:
            enrichment = selected_enrichment
    else:
        st.error("No enrichment selected")
        return

    init_test_enrichment_session_state()

    # Display success message if present
    if st.session_state.test_enrichment_success_message:
        st.success(st.session_state.test_enrichment_success_message)
        st.session_state.test_enrichment_success_message = None

    st.title(f"🧪 Test Enrichment - {enrichment['enrichment_name']}")
    st.info("Edit the enrichment configuration below. Saved changes will be reflected in the Review Enrichment page.")
    show_review_enrichment_page()
    st.divider()

    show_leads()
    st.divider()
    
    st.subheader("🧪 Edit Enrichment Configuration")
    show_goal_editor(enrichment)
    show_acceptable_evidence_editor(enrichment)
    show_result_format_editor(enrichment)
    st.divider()
    show_run_enrichment()

def show_review_enrichment_page():
    """Button to navigate back to the review enrichment page"""
    if st.button("📋 Back to Review Enrichment", width='stretch'):
        st.session_state.current_page = "review_enrichment"
        st.rerun()

def init_test_enrichment_session_state():
    """Initialize session state for test enrichment page."""
    current_project_id = st.session_state.selected_project.get("id") if st.session_state.selected_project else None
    if "test_enrichment_leads" not in st.session_state:
        st.session_state.test_enrichment_leads = {}
    if current_project_id and current_project_id not in st.session_state.test_enrichment_leads:
        st.session_state.test_enrichment_leads[current_project_id] = {"data": None, "columns": None, "count": 0}
    if "test_enrichment_success_message" not in st.session_state:
        st.session_state.test_enrichment_success_message = None


def show_leads():
    """Show first 10 leads for the current project (cached in session state)."""
    project = st.session_state.selected_project
    if not project:
        return
    project_id = project["id"]

    init_test_enrichment_session_state()

    st.subheader("📋 Test Leads")
    st.caption("Temporary test leads (session-only). Add or delete without touching the database.")

    leads_cache = st.session_state.test_enrichment_leads.get(project_id, {"data": None, "columns": None, "count": 0})

    if leads_cache["data"] is None:
        try:
            result = get_merged_results(project_id)
            if result and result.get("data"):
                leads_data = result["data"][:10]  # first 10 rows
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
            else:
                st.info("ℹ️ No leads available yet for this project.")
                return
        except Exception as e:
            st.error(f"❌ Error loading leads: {str(e)}")
            return

    import pandas as pd

    df = pd.DataFrame(leads_cache["data"])
    # Only show the "lead" column, exclude id, project_id, and serp_count
    display_columns = ["lead"] if "lead" in df.columns else []
    display_df = df[display_columns] if display_columns else df

    editor_key = f"test_enrichment_leads_editor_{project_id}"
    edited_df = st.data_editor(
        display_df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        key=editor_key,
    )

    if st.button("💾 Save Test Leads (session only)", key=f"save_test_leads_{project_id}", use_container_width=True):
        st.session_state.test_enrichment_leads[project_id] = {
            "data": edited_df.to_dict(orient="records"),
            "columns": list(edited_df.columns),
            "count": len(edited_df),
        }
        st.success("✅ Test leads saved in session (not persisted to the database).")
        st.rerun()

    total_session_leads = len(display_df)
    st.caption(f"Showing {total_session_leads} test lead(s) from session (not counting database).")


def show_run_enrichment():
    """Temporary stub to run enrichment on test leads (session only)."""
    project = st.session_state.selected_project
    if not project:
        return
    project_id = project["id"]
    leads_cache = st.session_state.test_enrichment_leads.get(project_id, {"data": []})

    st.subheader("🚀 Run Enrichment on Test Leads")
    if st.button("Run Enrichment (stub)", key=f"run_enrichment_stub_{project_id}", use_container_width=True):
        if not leads_cache.get("data"):
            st.warning("⚠️ No test leads available. Add or load leads above before running.")
        else:
            with st.spinner("Simulating enrichment on test leads..."):
                st.success(f"✅ Simulated enrichment on {len(leads_cache['data'])} test lead(s). (Backend not implemented)")

def show_goal_editor(enrichment):
    """Editable goal field"""
    st.write("**🎯 Goal:**")
    goal_key = f"enrichment_goal_edit_{enrichment['id']}"
    if goal_key not in st.session_state:
        st.session_state[goal_key] = enrichment.get('goal', '')

    st.text_area(
        "Goal",
        value=st.session_state[goal_key],
        key=goal_key,
        placeholder="Enter the goal for this enrichment...",
        height=100,
        label_visibility="collapsed",
        help="Describe what this enrichment is trying to achieve",
    )
    show_save_button(
        enrichment,
        field_key=goal_key,
        payload_key="goal",
        success_message="Goal saved"
    )

def show_acceptable_evidence_editor(enrichment):
    """Editable acceptable evidence field"""
    st.write("**📝 Acceptable Evidence:**")
    evidence_key = f"enrichment_acceptable_evidence_edit_{enrichment['id']}"
    if evidence_key not in st.session_state:
        st.session_state[evidence_key] = enrichment.get('acceptable_evidence', '')

    st.text_area(
        "Acceptable Evidence",
        value=st.session_state[evidence_key],
        key=evidence_key,
        placeholder="Enter acceptable evidence criteria...",
        height=100,
        label_visibility="collapsed",
        help="Describe what types of evidence are acceptable for this enrichment",
    )
    show_save_button(
        enrichment,
        field_key=evidence_key,
        payload_key="acceptable_evidence",
        success_message="Acceptable evidence saved"
    )

def show_result_format_editor(enrichment):
    """Editable result format field"""
    st.write("**📝 Result Format:**")
    format_key = f"enrichment_result_format_edit_{enrichment['id']}"
    true_if_key = f"{format_key}_true_if"
    false_if_key = f"{format_key}_false_if"
    number_def_key = f"{format_key}_number_def"
    text_def_key = f"{format_key}_text_def"
    
    if format_key not in st.session_state:
        current_format = enrichment.get('result_format', '')
        st.session_state[format_key] = current_format
    if true_if_key not in st.session_state:
        st.session_state[true_if_key] = enrichment.get('result_true_if', '')
    if false_if_key not in st.session_state:
        st.session_state[false_if_key] = enrichment.get('result_false_if', '')
    if number_def_key not in st.session_state:
        st.session_state[number_def_key] = enrichment.get('result_number_value', '')
    if text_def_key not in st.session_state:
        st.session_state[text_def_key] = enrichment.get('result_text_value', '')

    options = ["", "True/False", "Text", "Number"]
    current_index = 0
    if st.session_state[format_key] in options:
        current_index = options.index(st.session_state[format_key])

    st.selectbox(
        "Result Format",
        options=options,
        index=current_index,
        key=format_key,
        label_visibility="collapsed",
        help="Select the expected format for the enrichment result",
    )
    selected_format = st.session_state.get(format_key, "")

    payload = {"result_format": selected_format}

    if selected_format == "True/False":
        st.text_input(
            "True if",
            key=true_if_key,
            value=st.session_state[true_if_key],
            placeholder="Describe when the result should be True",
        )
        st.text_input(
            "False if",
            key=false_if_key,
            value=st.session_state[false_if_key],
            placeholder="Describe when the result should be False",
        )
        payload["result_true_if"] = st.session_state.get(true_if_key, "")
        payload["result_false_if"] = st.session_state.get(false_if_key, "")
        payload["result_number_value"] = ""
        payload["result_text_value"] = ""
    elif selected_format == "Number":
        st.text_input(
            "Define the Value",
            key=number_def_key,
            value=st.session_state[number_def_key],
            placeholder="Describe how the number should be calculated or formatted",
        )
        payload["result_number_value"] = st.session_state.get(number_def_key, "")
        payload["result_true_if"] = ""
        payload["result_false_if"] = ""
        payload["result_text_value"] = ""
    elif selected_format == "Text":
        st.text_input(
            "What do you want returned",
            key=text_def_key,
            value=st.session_state[text_def_key],
            placeholder="Describe the text that should be returned",
        )
        payload["result_text_value"] = st.session_state.get(text_def_key, "")
        payload["result_true_if"] = ""
        payload["result_false_if"] = ""
        payload["result_number_value"] = ""

    show_save_button_group(
        enrichment=enrichment,
        payload=payload,
        success_message="Result format saved",
    )

def show_save_button(enrichment, field_key, payload_key, success_message):
    """Show save button for a single field"""
    # Display success message if present for this field
    success_key = f"{field_key}_success"
    if st.session_state.get(success_key):
        st.success(st.session_state[success_key])
        st.session_state[success_key] = None
    
    if st.button("💾 Save", key=f"{field_key}_save", use_container_width=True):
        current_value = st.session_state.get(field_key, "")
        save_field(
            enrichment,
            {payload_key: current_value},
            success_message,
            success_key
        )

def show_save_button_group(enrichment, payload, success_message):
    """Show save button for a group of fields"""
    # Display success message if present for this group
    success_key = f"{list(payload.keys())[0]}_group_success"
    if st.session_state.get(success_key):
        st.success(st.session_state[success_key])
        st.session_state[success_key] = None
    
    if st.button("💾 Save", key=f"{list(payload.keys())[0]}_group_save", use_container_width=True):
        save_field_group(
            enrichment=enrichment,
            payload=payload,
            success_message=success_message,
            success_key=success_key
        )

def save_field(enrichment, payload, success_message, success_key):
    """Persist a single field and refresh session state"""
    with st.spinner("💾 Saving..."):
        try:
            result = update_enrichment_fields(enrichment["id"], **payload)
            if result and result.get("success"):
                st.session_state[success_key] = f"✅ {success_message}"
                st.session_state.test_enrichment_success_message = f"✅ {success_message}"
                updated = get_enrichment(enrichment["id"])
                if updated:
                    st.session_state.selected_enrichment = updated
                st.rerun()
            else:
                st.error(f"❌ Failed to save: {result.get('message', 'Unknown error') if result else 'No response from server'}")
        except Exception as e:
            st.error(f"❌ Error saving changes: {str(e)}")

def save_field_group(enrichment, payload, success_message, success_key):
    """Persist multiple related fields and refresh session state"""
    with st.spinner("💾 Saving..."):
        try:
            result = update_enrichment_fields(enrichment["id"], **payload)
            if result and result.get("success"):
                st.session_state[success_key] = f"✅ {success_message}"
                st.session_state.test_enrichment_success_message = f"✅ {success_message}"
                updated = get_enrichment(enrichment["id"])
                if updated:
                    st.session_state.selected_enrichment = updated
                st.rerun()
            else:
                st.error(f"❌ Failed to save: {result.get('message', 'Unknown error') if result else 'No response from server'}")
        except Exception as e:
            st.error(f"❌ Error saving changes: {str(e)}")