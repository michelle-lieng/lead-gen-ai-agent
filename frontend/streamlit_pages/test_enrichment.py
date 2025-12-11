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

    st.markdown(f"# 🧪 Test Enrichment - {enrichment['enrichment_name']}")
    st.markdown("---")
    
    # Back button
    if st.button("← Back to Review Enrichment", width='stretch'):
        st.session_state.current_page = "review_enrichment"
        st.rerun()
    
    st.markdown("---")
    
    # Editable enrichment configuration
    show_goal_editor(enrichment)
    show_acceptable_evidence_editor(enrichment)
    show_result_format_editor(enrichment)
    st.markdown("---")
    
    # Save button
    show_save_button(enrichment)
    st.markdown("---")

def show_goal_editor(enrichment):
    """Editable goal field"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 🎯 Goal:")
    with col2:
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
            help="Describe what this enrichment is trying to achieve"
        )

def show_acceptable_evidence_editor(enrichment):
    """Editable acceptable evidence field"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 📝 Acceptable Evidence:")
    with col2:
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
            help="Describe what types of evidence are acceptable for this enrichment"
        )

def show_result_format_editor(enrichment):
    """Editable result format field"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 📝 Result Format:")
    with col2:
        format_key = f"enrichment_result_format_edit_{enrichment['id']}"
        if format_key not in st.session_state:
            current_format = enrichment.get('result_format', '')
            st.session_state[format_key] = current_format
        
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
            help="Select the expected format for the enrichment result"
        )

def show_save_button(enrichment):
    """Save button to update enrichment fields"""
    if st.button("💾 Save Changes", type="primary", width='stretch'):
        goal_key = f"enrichment_goal_edit_{enrichment['id']}"
        evidence_key = f"enrichment_acceptable_evidence_edit_{enrichment['id']}"
        format_key = f"enrichment_result_format_edit_{enrichment['id']}"
        
        goal = st.session_state.get(goal_key, '')
        acceptable_evidence = st.session_state.get(evidence_key, '')
        result_format = st.session_state.get(format_key, '')
        
        with st.spinner("💾 Saving changes..."):
            try:
                result = update_enrichment_fields(
                    enrichment['id'],
                    goal=goal,
                    acceptable_evidence=acceptable_evidence,
                    result_format=result_format
                )
                if result and result.get('success'):
                    st.success("✅ Enrichment configuration saved successfully!")
                    # Refresh enrichment data
                    updated_enrichment = get_enrichment(enrichment['id'])
                    if updated_enrichment:
                        st.session_state.selected_enrichment = updated_enrichment
                    st.rerun()
                else:
                    st.error(f"❌ Failed to save: {result.get('message', 'Unknown error') if result else 'No response from server'}")
            except Exception as e:
                st.error(f"❌ Error saving changes: {str(e)}")

