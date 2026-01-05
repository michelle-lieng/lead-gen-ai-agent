"""
Project overview page
"""

import streamlit as st
from api import create_enrichment, get_enrichments, update_enrichment, delete_enrichment
from utils.display_errors import call_api


def show_enrichments():
    """Enrichment page"""
    selected_project = st.session_state.get("selected_project")
    project_id = selected_project["id"]

    # Initialize project-specific session state keys
    name_input_key = f"enrichment_name_form_input_{project_id}"
    description_input_key = f"enrichment_description_form_input_{project_id}"
    success_key = f"enrichment_create_success_{project_id}"

    st.session_state.setdefault(name_input_key, "")
    st.session_state.setdefault(description_input_key, "")

    st.markdown(f"# 📋 Enrichment - {selected_project['project_name']}")
    st.markdown("---")

    st.subheader("🔍 Create New Enrichment")

    with st.form(f"create_enrichment_form_{project_id}"):
        enrichment_name = st.text_input(
            "Enrichment Name*",
            placeholder="e.g. More than 1 doctor",
            key=name_input_key,
        )
        enrichment_description = st.text_area(
            "Self Notes [Optional]",
            placeholder="Enter your self notes here...",
            key=description_input_key,
        )

        submitted = st.form_submit_button("Create Enrichment", type="primary")

        if submitted:
            if not enrichment_name:
                st.error("Please enter an enrichment name")
            else:
                with st.spinner("Creating enrichment..."):
                    result = call_api(
                        create_enrichment,
                        project_id,
                        enrichment_name,
                        enrichment_description,
                    )
                    if result:
                        # Store success message in session state before clearing form and rerunning
                        st.session_state[success_key] = (
                            f"✅ Enrichment '{enrichment_name}' created successfully!"
                        )
                        # Clear form fields after successful creation by deleting the session state keys
                        if name_input_key in st.session_state:
                            del st.session_state[name_input_key]
                        if description_input_key in st.session_state:
                            del st.session_state[description_input_key]
                        st.rerun()
    if success_key in st.session_state:
        st.success(st.session_state[success_key])
        # Clear the success message after displaying it
        del st.session_state[success_key]

    st.markdown("---")

    # Enrichments overview
    st.subheader("📋 Your Enrichments")

    with st.spinner("Loading enrichments..."):
        enrichments = call_api(get_enrichments, project_id) or []

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
                    if enrichment.get("enrichment_description"):
                        st.caption(enrichment["enrichment_description"])
                    # Dates
                    created_date = enrichment["date_added"][:10]
                    updated_date = enrichment["last_updated"][:10]
                    st.caption(f"📅 Created: {created_date} | Updated: {updated_date}")

                with col2:
                    if st.button(
                        "🔍  Open", key=f"open_{project_id}_{enrichment['id']}"
                    ):
                        st.session_state.selected_enrichment = enrichment
                        st.session_state.current_page = "review_enrichment"
                        st.rerun()

                with col3:
                    edit_key = f"edit_mode_{project_id}_{enrichment['id']}"
                    if st.session_state.get(edit_key, False):
                        # In edit mode - show save/cancel buttons
                        if st.button(
                            "💾 Save",
                            key=f"save_{project_id}_{enrichment['id']}",
                            help="Save changes",
                            width="stretch",
                        ):
                            textarea_key = f"textarea_{project_id}_{enrichment['id']}"
                            name_input_key = (
                                f"name_input_{project_id}_{enrichment['id']}"
                            )
                            column_name_input_key = (
                                f"column_name_input_{project_id}_{enrichment['id']}"
                            )
                            new_description = st.session_state.get(
                                textarea_key,
                                enrichment.get("enrichment_description", ""),
                            )
                            new_name = st.session_state.get(
                                name_input_key, enrichment.get("enrichment_name", "")
                            )
                            new_column_name = st.session_state.get(
                                column_name_input_key, enrichment.get("column_name", "")
                            )
                            with st.spinner("Updating enrichment..."):
                                result = call_api(
                                    update_enrichment,
                                    enrichment["id"],
                                    enrichment_name=new_name,
                                    column_name=new_column_name,
                                    enrichment_description=new_description,
                                )
                                if result:
                                    st.success(f"✅ Enrichment updated successfully!")
                                    # Reset edit mode and clean up session state
                                    if edit_key in st.session_state:
                                        del st.session_state[edit_key]
                                    if textarea_key in st.session_state:
                                        del st.session_state[textarea_key]
                                    if name_input_key in st.session_state:
                                        del st.session_state[name_input_key]
                                    if column_name_input_key in st.session_state:
                                        del st.session_state[column_name_input_key]
                                    st.rerun()
                        if st.button(
                            "❌ Cancel",
                            key=f"cancel_edit_{project_id}_{enrichment['id']}",
                            help="Cancel editing",
                            width="stretch",
                        ):
                            textarea_key = f"textarea_{project_id}_{enrichment['id']}"
                            name_input_key = (
                                f"name_input_{project_id}_{enrichment['id']}"
                            )
                            column_name_input_key = (
                                f"column_name_input_{project_id}_{enrichment['id']}"
                            )
                            if edit_key in st.session_state:
                                del st.session_state[edit_key]
                            if textarea_key in st.session_state:
                                del st.session_state[textarea_key]
                            if name_input_key in st.session_state:
                                del st.session_state[name_input_key]
                            if column_name_input_key in st.session_state:
                                del st.session_state[column_name_input_key]
                            st.rerun()
                    else:
                        # Not in edit mode - show edit button
                        if st.button(
                            "✏️ Edit",
                            key=f"edit_{project_id}_{enrichment['id']}",
                            help="Edit enrichment",
                            width="stretch",
                        ):
                            st.session_state[edit_key] = True
                            st.rerun()

                with col4:
                    delete_key = f"delete_confirm_{project_id}_{enrichment['id']}"
                    # Check if we're in confirmation mode
                    if st.session_state.get(delete_key, False):
                        # Show confirm button instead
                        if st.button(
                            "✅",
                            key=f"confirm_delete_{project_id}_{enrichment['id']}",
                            help="Confirm deletion",
                            width="stretch",
                        ):
                            with st.spinner("Deleting enrichment..."):
                                success = call_api(delete_enrichment, enrichment["id"])
                                if success:
                                    st.success(
                                        f"✅ Enrichment '{enrichment['enrichment_name']}' deleted successfully!"
                                    )
                                    # Reset confirmation state
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    if (
                                        st.session_state.selected_enrichment
                                        and st.session_state.selected_enrichment["id"]
                                        == enrichment["id"]
                                    ):
                                        st.session_state.selected_enrichment = None
                                        st.session_state.current_page = "enrichment"
                                    st.rerun()
                        if st.button(
                            "❌",
                            key=f"cancel_delete_{project_id}_{enrichment['id']}",
                            help="Cancel deletion",
                            width="stretch",
                        ):
                            if delete_key in st.session_state:
                                del st.session_state[delete_key]
                            st.rerun()
                    else:
                        if st.button(
                            "🗑️",
                            key=f"delete_{project_id}_{enrichment['id']}",
                            help="Delete enrichment",
                            width="stretch",
                        ):
                            st.session_state[delete_key] = True
                            st.rerun()

                if st.session_state.get(
                    f"edit_mode_{project_id}_{enrichment['id']}", False
                ):
                    name_input_key = f"name_input_{project_id}_{enrichment['id']}"
                    column_name_input_key = (
                        f"column_name_input_{project_id}_{enrichment['id']}"
                    )
                    textarea_key = f"textarea_{project_id}_{enrichment['id']}"

                    # Initialize session state if not exists (Streamlit will use this automatically via key parameter)
                    if name_input_key not in st.session_state:
                        st.session_state[name_input_key] = enrichment.get(
                            "enrichment_name", ""
                        )
                    if column_name_input_key not in st.session_state:
                        st.session_state[column_name_input_key] = enrichment.get(
                            "column_name", ""
                        )
                    if textarea_key not in st.session_state:
                        st.session_state[textarea_key] = enrichment.get(
                            "enrichment_description", ""
                        )

                    st.text_input(
                        "Enrichment Name:",
                        key=name_input_key,
                        help="Edit the enrichment display name",
                    )

                    st.text_input(
                        "Column Name:",
                        key=column_name_input_key,
                        help="Edit the database column name (lowercase, underscores only)",
                    )

                    st.text_area("Edit Self Notes:", key=textarea_key, height=100)

                if st.session_state.get(
                    f"delete_confirm_{project_id}_{enrichment['id']}", False
                ):
                    st.warning(
                        f"⚠️ Are you sure you want to delete '{enrichment['enrichment_name']}'? Click ✅ to confirm or ❌ to cancel."
                    )

                st.markdown("---")
