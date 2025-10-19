"""
Streamlit frontend for Lead Gen AI Agent platform
"""
import streamlit as st

def main():
    st.set_page_config(
        page_title="AI Lead Generator",
        page_icon="🤖",
        layout="wide"
    )
    
    st.markdown("# AI Lead Generator")
    st.markdown("---")
    
    # Initialize session state for projects
    if 'projects' not in st.session_state:
        st.session_state.projects = []
    
    # Create new project section
    st.subheader("🚀 Create New Project")
    
    project_name = st.text_input("Project Name")
    
    if st.button("Create Project", type="primary"):
        if project_name:
            # Create new project
            new_project = {
                "id": f"project_{len(st.session_state.projects) + 1}",
                "name": project_name,
                "status": "Draft",
                "leads": 0,
                "last_updated": "Just now"
            }
            st.session_state.projects.append(new_project)
            st.success(f"Project '{project_name}' created!")
            st.rerun()
        else:
            st.error("Please enter a project name")
    
    st.markdown("---")
    
    # Old projects section
    st.subheader("📁 Your Projects")
    
    if not st.session_state.projects:
        st.info("No projects yet. Create your first project above!")
    else:
        for project in st.session_state.projects:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{project['name']}**")
                    st.caption(f"Last updated: {project['last_updated']}")
                
                with col2:
                    if project['status'] == 'Completed':
                        st.success(project['status'])
                    elif project['status'] == 'In Progress':
                        st.warning(project['status'])
                    else:
                        st.info(project['status'])
                
                with col3:
                    st.metric("Leads", project['leads'])
                
                with col4:
                    if st.button("Open", key=f"open_{project['id']}"):
                        st.info(f"Opening {project['name']}...")
                
                st.markdown("---")

if __name__ == "__main__":
    main()

