"""
Dashboard page - main project overview and creation
"""
import streamlit as st
from api import get_projects, create_project, delete_project, update_project
# ============================================================================
# STATE HELPERS - Only the essentials
# ============================================================================

def init_dashboard_state():
    """Initialize dashboard-specific session state"""
    if "project_name_form_input" not in st.session_state:
        st.session_state.project_name_form_input = ""
    if "project_description_form_input" not in st.session_state:
        st.session_state.project_description_form_input = ""

# ============================================================================
# UI SECTIONS - One function per major section
# ============================================================================

def render_create_project_section():
    """Render the create project form section"""
    # Create new project section
    st.subheader("🚀 Create New Project")

    with st.form("create_project_form"):
        project_name = st.text_input(
            "Project Name*", 
            placeholder="e.g. Seabin Leads",
            key="project_name_form_input"
        )
        description = st.text_area(
            "Self Notes [Optional]", 
            placeholder="Enter your self notes here...",
            key="project_description_form_input"
        )
        
        submitted = st.form_submit_button("Create Project", type="primary")
        
        if submitted:
            if not project_name:
                st.error("Please enter a project name")
            else:
                with st.spinner("Creating project..."):
                    try:
                        result = create_project(project_name, description)
                        if result:
                            # Store success message in session state before clearing form and rerunning
                            st.session_state.project_create_success = f"✅ Project '{project_name}' created successfully!"
                            # Clear form fields after successful creation by deleting the session state keys
                            if "project_name_form_input" in st.session_state:
                                del st.session_state.project_name_form_input
                            if "project_description_form_input" in st.session_state:
                                del st.session_state.project_description_form_input
                            st.rerun()
                    except Exception as e:
                        # Check error code from backend (DuplicateProjectNameError has code="DUPLICATE_PROJECT_NAME")
                        if hasattr(e, 'error_code') and e.error_code == "DUPLICATE_PROJECT_NAME":
                            st.error(f"❌ Project name '{project_name}' already exists. Please choose a different name and try again.")
                        else:
                            st.error(f"❌ Failed to create project: {str(e)}")
    
    # Display success message if it exists in session state
    if "project_create_success" in st.session_state:
        st.success(st.session_state.project_create_success)
        # Clear the success message after displaying it
        del st.session_state.project_create_success

def render_project_card(project: dict):
    # Main project info
    col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 1, 1, 0.8, 0.8])
    
    with col1:
        st.write(f"**{project['project_name']}**")
        if project.get('description'):
            st.caption(project['description'])
        
        # Dates
        created_date = project['date_added'][:10]
        updated_date = project['last_updated'][:10]
        st.caption(f"📅 Created: {created_date} | Updated: {updated_date}")
    
    with col2:
        st.metric("🎯 Leads", project.get('leads_collected',0))
    
    with col3:
        st.metric("📊 Datasets", project.get('datasets_added',0))
    
    with col4:
        st.metric("🔗 URLs", project.get('urls_processed', 0))
    
    with col5:
        if st.button("🔍 Open", key=f"open_{project['id']}"):
            st.session_state.selected_project = project
            st.session_state.current_page = "project_overview"
            st.rerun()
    
    with col6:
        edit_key = f"edit_mode_{project['id']}"
        if st.session_state.get(edit_key, False):
            # In edit mode - show save/cancel buttons
            if st.button("💾 Save", key=f"save_{project['id']}", help="Save changes", width='stretch'):
                textarea_key = f"textarea_{project['id']}"
                project_name_key = f"project_name_{project['id']}"
                new_description = st.session_state.get(textarea_key, project.get('description', ''))
                new_project_name = st.session_state.get(project_name_key, project.get('project_name', ''))
                
                # Validate project name is not empty
                if not new_project_name or not new_project_name.strip():
                    st.error("❌ Project name cannot be empty")
                else:
                    with st.spinner("Updating project..."):
                        try:
                            result = update_project(project['id'], project_name=new_project_name.strip(), description=new_description)
                            if result:
                                st.success(f"✅ Project updated successfully!")
                                # Reset edit mode and clean up session state
                                if edit_key in st.session_state:
                                    del st.session_state[edit_key]
                                if textarea_key in st.session_state:
                                    del st.session_state[textarea_key]
                                if project_name_key in st.session_state:
                                    del st.session_state[project_name_key]
                                st.rerun()
                        except Exception as e:
                            # Check error code from backend (DuplicateProjectNameError has code="DUPLICATE_PROJECT_NAME")
                            if hasattr(e, 'error_code') and e.error_code == "DUPLICATE_PROJECT_NAME":
                                st.error(f"❌ Project name '{new_project_name}' already exists. Please choose a different name.")
                            else:
                                st.error(f"❌ Failed to update project: {str(e)}")
            if st.button("❌ Cancel", key=f"cancel_edit_{project['id']}", help="Cancel editing", width='stretch'):
                textarea_key = f"textarea_{project['id']}"
                project_name_key = f"project_name_{project['id']}"
                if edit_key in st.session_state:
                    del st.session_state[edit_key]
                if textarea_key in st.session_state:
                    del st.session_state[textarea_key]
                if project_name_key in st.session_state:
                    del st.session_state[project_name_key]
                st.rerun()
        else:
            # Not in edit mode - show edit button
            if st.button("✏️ Edit", key=f"edit_{project['id']}", help="Edit self notes", width='stretch'):
                st.session_state[edit_key] = True
                st.rerun()
    
    with col7:
        delete_key = f"delete_confirm_{project['id']}"
        # Check if we're in confirmation mode
        if st.session_state.get(delete_key, False):
            # Show confirm button instead
            if st.button("✅", key=f"confirm_delete_{project['id']}", help="Confirm deletion", width='stretch'):
                with st.spinner("Deleting project..."):
                    success = delete_project(project['id'])
                    if success:
                        st.success(f"✅ Project '{project['project_name']}' deleted successfully!")
                        # Reset confirmation state
                        if delete_key in st.session_state:
                            del st.session_state[delete_key]
                        # Clear selected project if it was the deleted one
                        if st.session_state.selected_project and st.session_state.selected_project['id'] == project['id']:
                            st.session_state.selected_project = None
                            st.session_state.current_page = "dashboard"
                        st.rerun()
            # Cancel button
            if st.button("❌", key=f"cancel_delete_{project['id']}", help="Cancel deletion", width='stretch'):
                if delete_key in st.session_state:
                    del st.session_state[delete_key]
                st.rerun()
        else:
            # Initial delete button
            if st.button("🗑️", key=f"delete_{project['id']}", help="Delete project", width='stretch'):
                st.session_state[delete_key] = True
                st.rerun()
    
    # Show edit fields if in edit mode
    if st.session_state.get(f"edit_mode_{project['id']}", False):
        project_name_key = f"project_name_{project['id']}"
        textarea_key = f"textarea_{project['id']}"
        
        # Initialize the values if not already set
        if project_name_key not in st.session_state:
            st.session_state[project_name_key] = project.get('project_name', '')
        if textarea_key not in st.session_state:
            st.session_state[textarea_key] = project.get('description', '')
        
        st.text_input(
            "Project Name:",
            key=project_name_key,
            placeholder="Enter project name..."
        )
        
        st.text_area(
            "Self Notes:",
            key=textarea_key,
            placeholder="Enter your self notes here...",
            height=100
        )
    
    # Show confirmation message if delete was clicked
    if st.session_state.get(f"delete_confirm_{project['id']}", False):
        st.warning(f"⚠️ Are you sure you want to delete '{project['project_name']}'? Click ✅ to confirm or ❌ to cancel.")
    
    st.markdown("---")

# ============================================================================
# MAIN PAGE
# ============================================================================

def show_dashboard():
    """Main dashboard - project overview and creation"""
    st.markdown("# 🤖 AI Lead Generator Dashboard")
    st.markdown("---")

    # Create new project section
    render_create_project_section()
    st.markdown("---")
    
    # Your projects section
    st.subheader("📁 Your Projects")
    
    with st.spinner("Loading projects..."):
        projects = get_projects()
    
    if not projects:
        st.info("No projects yet. Create your first project above!")
    else:
        st.write(f"**Found {len(projects)} project(s)**")
        st.markdown("---")
        
        for project in projects:
            with st.container():
                render_project_card(project)
