"""
Lead collection page
"""
import streamlit as st
from api_client import update_project, generate_queries, generate_urls, generate_leads

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
    
    # Step 1: Editable project description (always loaded from database)
    st.markdown("**Step 1: Project Description**")
    
    # Get description from database (via project object)
    current_description = project.get('description', '')
    # Editable description with inline save
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
    
    # Step 2: Generate search queries (uses description from database)
    st.markdown("**Step 2: AI-Generated Search Queries**")
    
    if st.button("🤖 Generate Smart Search Queries"):
        with st.spinner("🤖 AI is generating targeted search queries..."):
            generated_queries = generate_queries(project['id'])
            if generated_queries:
                st.session_state.generated_queries = generated_queries
                st.success(f"✅ Generated {len(generated_queries)} search queries!")
            else:
                st.error("❌ Failed to generate queries. Please try again.")
    
    # Step 3: Display and edit queries (always show if queries exist)
    if 'generated_queries' in st.session_state:
        st.markdown("**Review and customize your search queries:**")
        
        for i, query in enumerate(st.session_state.generated_queries):
            col1, col2 = st.columns([4, 1])
            with col1:
                edited_query = st.text_input(
                    f"Query {i+1}", 
                    value=query, 
                    key=f"query_{i}",
                    label_visibility="collapsed"
                )
                # Update the query in session state if edited (only if not empty)
                if edited_query.strip() != query and edited_query.strip():
                    st.session_state.generated_queries[i] = edited_query.strip()
                elif edited_query.strip() == "" and query:
                    # If user cleared it, remove it instead
                    st.session_state.generated_queries.pop(i)
                    st.rerun()
            with col2:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.generated_queries.pop(i)
                    st.rerun()
        
        # Add new query
        st.markdown("**Add your own search queries:**")
        new_query = st.text_input("Add custom query", placeholder="Enter your own search query...")
        if st.button("➕ Add Query") and new_query:
            st.session_state.generated_queries.append(new_query.strip())
            st.rerun()
        
        # Step 4: Start search
        st.markdown("**Step 3: Start the search**")
        if st.button("🔍 Start Web Search", type="primary"):
            if st.session_state.generated_queries:
                with st.spinner("🔍 Starting web search..."):
                    # Step 1: Generate URLs from queries
                    st.info(f"📊 Generating URLs from {len(st.session_state.generated_queries)} queries...")
                    urls_result = generate_urls(project['id'], st.session_state.generated_queries)
                    
                    if urls_result:
                        st.success(f"✅ Found URLs from search results")
                        
                        # Step 2: Extract leads from URLs
                        st.info("🤖 Extracting leads from URLs...")
                        leads_result = generate_leads(project['id'])
                        
                        if leads_result:
                            st.success("✅ Leads extracted successfully!")
                            st.markdown("**📊 Search Results:**")
                            st.success(f"✅ Successfully processed {len(st.session_state.generated_queries)} search queries and extracted leads!")
                        else:
                            st.error("❌ Failed to extract leads. URLs were generated successfully.")
                    else:
                        st.error("❌ Failed to generate URLs from queries.")
            else:
                st.error("❌ Please add at least one query before starting the search.")

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
