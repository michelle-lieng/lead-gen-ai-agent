"""
Lead collection page
"""
import streamlit as st
from api_client import update_project

def show_collect_leads():
    """Lead collection page"""
    project = st.session_state.selected_project
    st.markdown(f"# 🎯 Collect Leads - {project['project_name']}")
    st.markdown("---")
    
    st.markdown("### 🔍 Lead Collection Tools")
    
    # Lead collection methods - 3 ways to collect leads
    tab1, tab2, tab3 = st.tabs(["🌐 Web Search", "📧 Email Scraping", "📁 Upload Dataset"])
    
    with tab1:
        show_web_search_tab(project)
    
    with tab2:
        show_email_scraping_tab(project)
    
    with tab3:
        show_upload_dataset_tab(project)

def show_web_search_tab(project):
    """Web search tab content"""
    st.markdown("#### 🧠 AI-Powered Web Search")
    
    # Step 1: Editable project description
    st.markdown("**Step 1: Project Description**")
    
    # Editable description with inline save
    current_description = project.get('description', '')
    updated_description = st.text_area(
        "Edit your project description", 
        value=current_description,
        placeholder="e.g., Find sustainable energy companies in California that are focused on solar and wind power, preferably startups or mid-size companies with 10-500 employees...",
        height=100,
        help="Describe your target companies. Be specific about industry, location, company size, and any other criteria"
    )
    
    # Inline save button
    if st.button("💾 Save"):
        with st.spinner("Saving..."):
            result = update_project(project['id'], description=updated_description)
            if result:
                st.success("✅ Description updated!")
                # Update the project in session state
                st.session_state.selected_project = result
                st.rerun()
            else:
                st.error("❌ Failed to update description")
    
    if updated_description:
        # Step 2: Generate search queries
        st.markdown("**Step 2: AI-Generated Search Queries**")
        if st.button("🤖 Generate Smart Search Queries"):
            with st.spinner("🤖 AI is generating targeted search queries..."):
                # TODO: Call AI service to generate search queries based on updated_description
                generated_queries = [
                    "sustainable energy companies California solar wind",
                    "green tech startups California renewable energy",
                    "clean energy companies Bay Area 10-500 employees",
                    "solar panel manufacturers California",
                    "wind energy companies California startups"
                ]
                st.session_state.generated_queries = generated_queries
        
        # Step 3: Display and edit queries
        if 'generated_queries' in st.session_state:
            st.markdown("**Review and customize your search queries:**")
            
            final_queries = []
            for i, query in enumerate(st.session_state.generated_queries):
                col1, col2 = st.columns([4, 1])
                with col1:
                    edited_query = st.text_input(
                        f"Query {i+1}", 
                        value=query, 
                        key=f"query_{i}",
                        label_visibility="collapsed"
                    )
                    final_queries.append(edited_query)
                with col2:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.generated_queries.pop(i)
                        st.rerun()
            
            # Add new query
            st.markdown("**Add your own search queries:**")
            new_query = st.text_input("Add custom query", placeholder="Enter your own search query...")
            if st.button("➕ Add Query") and new_query:
                st.session_state.generated_queries.append(new_query)
                st.rerun()
            
            # Step 4: Start search
            st.markdown("**Step 3: Start the search**")
            if st.button("🔍 Start Web Search", type="primary"):
                with st.spinner("🔍 Searching the web with all queries..."):
                    # TODO: Implement SerpAPI search for each query
                    st.info(f"🔍 Searching with {len(final_queries)} queries...")
                    st.info("📊 Extracting URLs from search results...")
                    st.info("✅ Search completed! Found X potential leads.")
                    
                    # Show results
                    st.markdown("**📊 Search Results:**")
                    st.success("✅ Found 150 potential leads from 5 search queries")
                    
                    # Show sample results
                    sample_results = [
                        {"url": "https://solarcorp.com", "title": "SolarCorp - Leading Solar Solutions", "snippet": "California-based solar company..."},
                        {"url": "https://windpower.com", "title": "WindPower Inc - Renewable Energy", "snippet": "Wind energy solutions for California..."},
                        {"url": "https://greentech.com", "title": "GreenTech Solutions", "snippet": "Sustainable energy startup in Bay Area..."}
                    ]
                    
                    for result in sample_results:
                        with st.container():
                            st.write(f"**{result['title']}**")
                            st.caption(f"🔗 {result['url']}")
                            st.caption(result['snippet'])
                            st.markdown("---")

def show_email_scraping_tab(project):
    """Email scraping tab content"""
    st.markdown("#### Extract emails from websites")
    website_url = st.text_input("Website URL", placeholder="https://example.com")
    if st.button("📧 Extract Emails"):
        st.info("📧 Extracting emails from website...")
        # TODO: Implement email extraction

def show_upload_dataset_tab(project):
    """Upload dataset tab content"""
    st.markdown("#### Upload existing dataset")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file with company data",
        key="dataset_upload"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Preview data
        if st.button("👀 Preview Data"):
            st.markdown("#### 📊 Data Preview")
            st.info("Preview functionality coming soon!")
    
    st.markdown("---")
    st.markdown("#### 📋 Existing Datasets")
    st.info("No datasets uploaded yet. Upload your first dataset above!")
    
    st.markdown("---")
    st.markdown("### 📊 Current Leads")
    st.info("No leads collected yet. Use the tools above to start collecting leads!")
