"""
Test enrichment page - edit enrichment configuration
"""
import streamlit as st
from api_client import get_enrichment, update_enrichment_fields

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

    st.title(f"🧪 Test Enrichment - {enrichment['enrichment_name']}")
    st.info("Edit the enrichment configuration below. Saved changes will be reflected in the Review Enrichment page.")
    show_review_enrichment_page()
    st.divider()
    
    st.subheader("🧪 Edit Enrichment Configuration")
    show_goal_editor(enrichment)
    show_acceptable_evidence_editor(enrichment)
    show_result_format_editor(enrichment)
    st.divider()

def show_review_enrichment_page():
    """Button to navigate back to the review enrichment page"""
    if st.button("📋 Back to Review Enrichment", width='stretch'):
        st.session_state.current_page = "review_enrichment"
        st.rerun()

def show_goal_editor(enrichment):
    """Editable goal field"""
    st.write("**🎯 Goal:**")
    goal_key = f"enrichment_goal_edit_{enrichment['id']}"
    goal_baseline_key = f"{goal_key}_baseline"
    goal_dirty_key = f"{goal_key}_dirty"
    if goal_key not in st.session_state:
        st.session_state[goal_key] = enrichment.get('goal', '')
    if goal_baseline_key not in st.session_state:
        st.session_state[goal_baseline_key] = st.session_state[goal_key]
    if goal_dirty_key not in st.session_state:
        st.session_state[goal_dirty_key] = False
    
    st.text_area(
        "Goal",
        value=st.session_state[goal_key],
        key=goal_key,
        placeholder="Enter the goal for this enrichment...",
        height=100,
        label_visibility="collapsed",
        help="Describe what this enrichment is trying to achieve",
        on_change=mark_dirty,
        args=(goal_dirty_key,)
    )
    show_save_if_dirty(
        enrichment,
        field_key=goal_key,
        baseline_key=goal_baseline_key,
        dirty_key=goal_dirty_key,
        payload_key="goal",
        success_message="Goal saved"
    )

def show_acceptable_evidence_editor(enrichment):
    """Editable acceptable evidence field"""
    st.write("**📝 Acceptable Evidence:**")
    evidence_key = f"enrichment_acceptable_evidence_edit_{enrichment['id']}"
    evidence_baseline_key = f"{evidence_key}_baseline"
    evidence_dirty_key = f"{evidence_key}_dirty"
    if evidence_key not in st.session_state:
        st.session_state[evidence_key] = enrichment.get('acceptable_evidence', '')
    if evidence_baseline_key not in st.session_state:
        st.session_state[evidence_baseline_key] = st.session_state[evidence_key]
    if evidence_dirty_key not in st.session_state:
        st.session_state[evidence_dirty_key] = False
    
    st.text_area(
        "Acceptable Evidence",
        value=st.session_state[evidence_key],
        key=evidence_key,
        placeholder="Enter acceptable evidence criteria...",
        height=100,
        label_visibility="collapsed",
        help="Describe what types of evidence are acceptable for this enrichment",
        on_change=mark_dirty,
        args=(evidence_dirty_key,)
    )
    show_save_if_dirty(
        enrichment,
        field_key=evidence_key,
        baseline_key=evidence_baseline_key,
        dirty_key=evidence_dirty_key,
        payload_key="acceptable_evidence",
        success_message="Acceptable evidence saved"
    )

def show_result_format_editor(enrichment):
    """Editable result format field"""
    st.write("**📝 Result Format:**")
    format_key = f"enrichment_result_format_edit_{enrichment['id']}"
    format_baseline_key = f"{format_key}_baseline"
    format_dirty_key = f"{format_key}_dirty"
    true_if_key = f"{format_key}_true_if"
    true_if_baseline_key = f"{true_if_key}_baseline"
    true_if_dirty_key = f"{true_if_key}_dirty"
    false_if_key = f"{format_key}_false_if"
    false_if_baseline_key = f"{false_if_key}_baseline"
    false_if_dirty_key = f"{false_if_key}_dirty"
    number_def_key = f"{format_key}_number_def"
    number_def_baseline_key = f"{number_def_key}_baseline"
    number_def_dirty_key = f"{number_def_key}_dirty"
    text_def_key = f"{format_key}_text_def"
    text_def_baseline_key = f"{text_def_key}_baseline"
    text_def_dirty_key = f"{text_def_key}_dirty"
    if format_key not in st.session_state:
        current_format = enrichment.get('result_format', '')
        st.session_state[format_key] = current_format
    if format_baseline_key not in st.session_state:
        st.session_state[format_baseline_key] = st.session_state[format_key]
    if format_dirty_key not in st.session_state:
        st.session_state[format_dirty_key] = False
    if true_if_key not in st.session_state:
        st.session_state[true_if_key] = enrichment.get('result_true_if', '')
    if true_if_baseline_key not in st.session_state:
        st.session_state[true_if_baseline_key] = st.session_state[true_if_key]
    if true_if_dirty_key not in st.session_state:
        st.session_state[true_if_dirty_key] = False
    if false_if_key not in st.session_state:
        st.session_state[false_if_key] = enrichment.get('result_false_if', '')
    if false_if_baseline_key not in st.session_state:
        st.session_state[false_if_baseline_key] = st.session_state[false_if_key]
    if false_if_dirty_key not in st.session_state:
        st.session_state[false_if_dirty_key] = False
    if number_def_key not in st.session_state:
        st.session_state[number_def_key] = enrichment.get('result_number_value', '')
    if number_def_baseline_key not in st.session_state:
        st.session_state[number_def_baseline_key] = st.session_state[number_def_key]
    if number_def_dirty_key not in st.session_state:
        st.session_state[number_def_dirty_key] = False
    if text_def_key not in st.session_state:
        st.session_state[text_def_key] = enrichment.get('result_text_value', '')
    if text_def_baseline_key not in st.session_state:
        st.session_state[text_def_baseline_key] = st.session_state[text_def_key]
    if text_def_dirty_key not in st.session_state:
        st.session_state[text_def_dirty_key] = False
    
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
        on_change=mark_dirty,
        args=(format_dirty_key,)
    )
    selected_format = st.session_state.get(format_key, "")

    payload = {"result_format": selected_format}
    dirty_keys = [format_dirty_key]
    baselines = [(format_baseline_key, format_key)]

    if selected_format == "True/False":
        st.text_input(
            "True if",
            key=true_if_key,
            value=st.session_state[true_if_key],
            placeholder="Describe when the result should be True",
            on_change=mark_dirty,
            args=(true_if_dirty_key,),
        )
        st.text_input(
            "False if",
            key=false_if_key,
            value=st.session_state[false_if_key],
            placeholder="Describe when the result should be False",
            on_change=mark_dirty,
            args=(false_if_dirty_key,),
        )
        payload["result_true_if"] = st.session_state.get(true_if_key, "")
        payload["result_false_if"] = st.session_state.get(false_if_key, "")
        dirty_keys.extend([true_if_dirty_key, false_if_dirty_key])
        baselines.extend([
            (true_if_baseline_key, true_if_key),
            (false_if_baseline_key, false_if_key),
        ])
    elif selected_format == "Number":
        st.text_input(
            "Define the Value",
            key=number_def_key,
            value=st.session_state[number_def_key],
            placeholder="Describe how the number should be calculated or formatted",
            on_change=mark_dirty,
            args=(number_def_dirty_key,),
        )
        payload["result_number_value"] = st.session_state.get(number_def_key, "")
        dirty_keys.append(number_def_dirty_key)
        baselines.append((number_def_baseline_key, number_def_key))
    elif selected_format == "Text":
        st.text_input(
            "What do you want returned",
            key=text_def_key,
            value=st.session_state[text_def_key],
            placeholder="Describe the text that should be returned",
            on_change=mark_dirty,
            args=(text_def_dirty_key,),
        )
        payload["result_text_value"] = st.session_state.get(text_def_key, "")
        dirty_keys.append(text_def_dirty_key)
        baselines.append((text_def_baseline_key, text_def_key))

    show_save_if_dirty_group(
        enrichment=enrichment,
        dirty_keys=dirty_keys,
        baselines=baselines,
        payload=payload,
        success_message="Result format saved"
    )

def mark_dirty(dirty_key: str):
    """Mark a field as dirty when the input changes."""
    st.session_state[dirty_key] = True

def show_save_if_dirty(enrichment, field_key, baseline_key, dirty_key, payload_key, success_message):
    """Show save button only when field differs from its baseline"""
    current_value = st.session_state.get(field_key, "")
    baseline_value = st.session_state.get(baseline_key, "")
    is_dirty = st.session_state.get(dirty_key, False) or current_value != baseline_value
    if is_dirty:
        if st.button("💾 Save", key=f"{field_key}_save", use_container_width=True):
            save_field(
                enrichment,
                {payload_key: current_value},
                success_message,
                baseline_key,
                dirty_key,
                current_value
            )

def show_save_if_dirty_group(enrichment, dirty_keys, baselines, payload, success_message):
    """Show save button when any field in the group is dirty"""
    is_dirty = False
    for dirty_key, (baseline_key, value_key) in zip(
        dirty_keys,
        baselines + [baselines[-1]] * max(0, len(dirty_keys) - len(baselines))
    ):
        current_value = st.session_state.get(value_key, "")
        baseline_value = st.session_state.get(baseline_key, "")
        if st.session_state.get(dirty_key, False) or current_value != baseline_value:
            is_dirty = True
            break
    if is_dirty:
        if st.button("💾 Save", key=f"{list(payload.keys())[0]}_group_save", use_container_width=True):
            save_field_group(
                enrichment=enrichment,
                payload=payload,
                success_message=success_message,
                baselines=baselines,
                dirty_keys=dirty_keys
            )

def save_field(enrichment, payload, success_message, baseline_key, dirty_key, new_baseline_value):
    """Persist a single field and refresh session state"""
    with st.spinner("💾 Saving..."):
        try:
            result = update_enrichment_fields(enrichment["id"], **payload)
            if result and result.get("success"):
                st.success(f"✅ {success_message}")
                st.session_state[baseline_key] = new_baseline_value
                st.session_state[dirty_key] = False
                updated = get_enrichment(enrichment["id"])
                if updated:
                    st.session_state.selected_enrichment = updated
                st.rerun()
            else:
                st.error(f"❌ Failed to save: {result.get('message', 'Unknown error') if result else 'No response from server'}")
        except Exception as e:
            st.error(f"❌ Error saving changes: {str(e)}")

def save_field_group(enrichment, payload, success_message, baselines, dirty_keys):
    """Persist multiple related fields and refresh session state"""
    with st.spinner("💾 Saving..."):
        try:
            result = update_enrichment_fields(enrichment["id"], **payload)
            if result and result.get("success"):
                st.success(f"✅ {success_message}")
                for baseline_key, value_key in baselines:
                    st.session_state[baseline_key] = st.session_state.get(value_key, "")
                for dirty_key in dirty_keys:
                    st.session_state[dirty_key] = False
                updated = get_enrichment(enrichment["id"])
                if updated:
                    st.session_state.selected_enrichment = updated
                st.rerun()
            else:
                st.error(f"❌ Failed to save: {result.get('message', 'Unknown error') if result else 'No response from server'}")
        except Exception as e:
            st.error(f"❌ Error saving changes: {str(e)}")

