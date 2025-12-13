"""
Project overview page
"""
import streamlit as st
from api_client import get_project, update_project, create_enrichment, get_enrichments, update_enrichment, delete_enrichment

def show_enrichments():
    """Enrichment page"""
    st.markdown("# 📋 Enrichment")
    st.markdown("---")
    
    st.subheader("🔍 Create New Enrichment")

    if "enrichment_name_form_input" not in st.session_state:
        st.session_state.enrichment_name_form_input = ""
    if "enrichment_description_form_input" not in st.session_state:
        st.session_state.enrichment_description_form_input = ""

    with st.form("create_enrichment_form"):
        enrichment_name = st.text_input(
            "Enrichment Name*",
            placeholder="e.g. company_size (No Spaces)",
            key="enrichment_name_form_input"
        )
        enrichment_description = st.text_area(
            "Self Notes [Optional]",
            placeholder="Enter your self notes here...",
            key="enrichment_description_form_input"
        )

        submitted = st.form_submit_button("Create Enrichment", type="primary")

        if submitted:
            if not enrichment_name:
                st.error("Please enter an enrichment name")
            else:
                with st.spinner("Creating enrichment..."):
                    try:
                        result = create_enrichment(enrichment_name, enrichment_description)
                        if result:
                            #Store success message in session state before clearing form and rerunning
                            st.session_state.enrichment_create_success = f"✅ Enrichment '{enrichment_name}' created successfully!"
                            # Clear form fields after successful creation by deleting the session state keys
                            if "enrichment_name_form_input" in st.session_state:
                                del st.session_state.enrichment_name_form_input
                            if "enrichment_description_form_input" in st.session_state:
                                del st.session_state.enrichment_description_form_input
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating enrichment: {e}")
                        if "already exists" in str(e).lower():
                            st.error(f"❌ Enrichment name '{enrichment_name}' already exists. Please choose a different name and try again.")
                        else:
                            st.error(f"❌ Failed to create enrichment: {e}")
    if "enrichment_create_success" in st.session_state:
        st.success(st.session_state.enrichment_create_success)
        # Clear the success message after displaying it
        del st.session_state.enrichment_create_success

    st.markdown("---")
    
    # Enrichments overview
    st.subheader("📋 Your Enrichments")
    
    with st.spinner("Loading enrichments..."):
        enrichments = get_enrichments()

    if not enrichments:
        st.info("No enrichments yet. Create your first enrichment above!")
    else:
        st.write(f"**Found {len(enrichments)} enrichment(s)**")
        st.markdown("---")

        for enrichment in enrichments:
            with st.container():
                # Main enrichment info
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{enrichment['enrichment_name']}**")
                    if enrichment.get('enrichment_description'):
                        st.caption(enrichment['enrichment_description'])
                    # Dates
                    created_date = enrichment['date_added'][:10]
                    updated_date = enrichment['last_updated'][:10]
                    st.caption(f"📅 Created: {created_date} | Updated: {updated_date}")
                
                with col2:
                    if st.button("🔍  Open", key=f"open_{enrichment['id']}"):
                        st.session_state.selected_enrichment = enrichment
                        st.session_state.current_page = "review_enrichment"
                        st.rerun()
                
                with col3: 
                    edit_key = f"edit_mode_{enrichment['id']}"
                    if st.session_state.get(edit_key, False):
                        # In edit mode - show save/cancel buttons
                        if st.button("💾 Save", key=f"save_{enrichment['id']}", help="Save changes", width='stretch'):
                            textarea_key = f"textarea_{enrichment['id']}"
                            new_description = st.session_state.get(textarea_key, enrichment.get('enrichment_description', ''))
                            with st.spinner("Updating enrichment..."):
                                result = update_enrichment(enrichment['id'], enrichment_description=new_description)
                                if result:
                                    st.success(f"✅ Enrichment '{enrichment['enrichment_name']}' updated successfully!")
                                    # Reset edit mode and clean up session state
                                    if edit_key in st.session_state:
                                        del st.session_state[edit_key]
                                    if textarea_key in st.session_state:
                                        del st.session_state[textarea_key]
                                    st.rerun()
                        if st.button("❌ Cancel", key=f"cancel_edit_{enrichment['id']}", help="Cancel editing", width='stretch'):
                            textarea_key = f"textarea_{enrichment['id']}"
                            if edit_key in st.session_state:
                                del st.session_state[edit_key]
                            if textarea_key in st.session_state:
                                del st.session_state[textarea_key]
                            st.rerun()
                    else:
                        # Not in edit mode - show edit button
                        if st.button("✏️ Edit", key=f"edit_{enrichment['id']}", help="Edit enrichment", width='stretch'):
                            st.session_state[edit_key] = True
                            st.rerun()
                
                with col4:
                    delete_key = f"delete_confirm_{enrichment['id']}"
                    # Check if we're in confirmation mode
                    if st.session_state.get(delete_key, False):
                        # Show confirm button instead
                        if st.button("✅", key=f"confirm_delete_{enrichment['id']}", help="Confirm deletion", width='stretch'):
                            with st.spinner("Deleting enrichment..."):
                                success = delete_enrichment(enrichment['id'])
                                if success:
                                    st.success(f"✅ Enrichment '{enrichment['enrichment_name']}' deleted successfully!")
                                    # Reset confirmation state
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    if st.session_state.selected_enrichment and st.session_state.selected_enrichment['id'] == enrichment['id']:
                                        st.session_state.selected_enrichment = None
                                        st.session_state.current_page = "enrichment"
                                    st.rerun()
                        if st.button("❌", key=f"cancel_delete_{enrichment['id']}", help="Cancel deletion", width='stretch'):
                            if delete_key in st.session_state:
                                del st.session_state[delete_key]
                            st.rerun()
                    else:
                        if st.button("🗑️", key=f"delete_{enrichment['id']}", help="Delete enrichment", width='stretch'):
                            st.session_state[delete_key] = True
                            st.rerun()
                    
                if st.session_state.get(f"edit_mode_{enrichment['id']}", False):
                    textarea_key = f"textarea_{enrichment['id']}"

                    if textarea_key not in st.session_state:
                        st.session_state[textarea_key] = enrichment.get('enrichment_description', '')

                    st.text_area(
                        "Edit Self Notes:",
                        value=st.session_state[textarea_key],
                        key=textarea_key,
                        placeholder="Enter your self notes here...",
                        height=100
                    )

                if st.session_state.get(f"delete_confirm_{enrichment['id']}", False):
                    st.warning(f"⚠️ Are you sure you want to delete '{enrichment['enrichment_name']}'? Click ✅ to confirm or ❌ to cancel.")
                
                st.markdown("---")