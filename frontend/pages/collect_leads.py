"""
Lead collection page
"""
import streamlit as st
import pandas as pd
from api_client import update_project, generate_queries, generate_urls, generate_leads, fetch_latest_run_zip, get_project, upload_dataset, fetch_datasets_zip

def fetch_and_store_zip_data(project_id: int):
    """Fetch ZIP file from API and store in session state"""
    zip_content, filename = fetch_latest_run_zip(project_id)
    if zip_content and filename:
        st.session_state["csv_data_all"] = zip_content
        st.session_state["csv_filename_all"] = filename
        return True
    return False

def fetch_and_store_datasets_zip(project_id: int):
    """Fetch dataset ZIP file from API and store in session state"""
    zip_content, filename = fetch_datasets_zip(project_id)
    if zip_content and filename:
        st.session_state["datasets_zip_data"] = zip_content
        st.session_state["datasets_zip_filename"] = filename
        return True
    return False

def show_collect_leads():
    """Lead collection page"""
    project = st.session_state.selected_project
    st.markdown(f"# 🎯 Collect Leads - {project['project_name']}")
    st.markdown("---")
    
    st.markdown("### 🔍 Lead Collection Tools")
    
    # Lead collection methods - 3 ways to collect leads
    tab1, tab2 = st.tabs(["🌐 Web Search", "📁 Upload Dataset"])
    
    with tab1:
        show_web_search_tab(project)
    
    with tab2:
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
        height=250,
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
    
    # Step 2: Search Queries
    st.markdown("**Step 2: Search Queries**")
    
    # Initialize queries dict if it doesn't exist (use dict for easy deletion by ID)
    if 'generated_queries' not in st.session_state:
        st.session_state.generated_queries = {}
    # Counter for unique IDs
    if 'query_counter' not in st.session_state:
        st.session_state.query_counter = 0
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Add your own search queries:**")
        # Use a form to handle input clearing properly
        with st.form("add_query_form", clear_on_submit=True):
            new_query = st.text_input("Add custom query", placeholder="Enter your own search query...", key="new_query_input")
            submitted = st.form_submit_button("➕ Add Query")
            if submitted and new_query and new_query.strip():
                query_id = f"q{st.session_state.query_counter}"
                st.session_state.query_counter += 1
                st.session_state.generated_queries[query_id] = new_query.strip()
                st.rerun()
    
    with col2:
        st.markdown("**Or generate AI queries:**")
        if st.button("🤖 Generate Smart Queries"):
            with st.spinner("🤖 AI is generating targeted search queries..."):
                generated_queries = generate_queries(project['id'])
                if generated_queries:
                    # Assign unique IDs to all new AI queries
                    for query in generated_queries:
                        query_id = f"q{st.session_state.query_counter}"
                        st.session_state.query_counter += 1
                        st.session_state.generated_queries[query_id] = query
                    st.success(f"✅ Generated {len(generated_queries)} search queries!")
                    st.rerun()
                else:
                    st.error("❌ Failed to generate queries. Please try again.")
    
    # Display and edit queries (always show if queries exist)
    if st.session_state.generated_queries:
        st.markdown("**Your search queries:**")
        
        queries_to_delete = []
        queries_list = list(st.session_state.generated_queries.items())  # Convert to list for display order
        
        for i, (query_id, query) in enumerate(queries_list):
            query_key = f"query_{query_id}"
            delete_key = f"remove_{query_id}"
            
            col1, col2 = st.columns([4, 1])
            with col1:
                edited_query = st.text_input(
                    f"Query {i+1}", 
                    value=query, 
                    key=query_key,
                    label_visibility="collapsed"
                )
                # Update the query in session state if edited
                if edited_query.strip() != query:
                    if edited_query.strip():  # Not empty - update it
                        st.session_state.generated_queries[query_id] = edited_query.strip()
                    else:  # Empty - mark for deletion
                        queries_to_delete.append(query_id)
            with col2:
                if st.button("❌", key=delete_key):
                    queries_to_delete.append(query_id)
        
        # Delete marked queries (simple - just remove from dict!)
        if queries_to_delete:
            for query_id in queries_to_delete:
                st.session_state.generated_queries.pop(query_id, None)
            st.rerun()
        
        # Step 3: Start search
        st.markdown("**Step 3: Start the search**")
        if st.button("🔍 Start Web Search", type="primary"):
            if st.session_state.generated_queries:
                with st.spinner("🔍 Starting web search..."):
                    # Convert dict to list for API call
                    queries_list = list(st.session_state.generated_queries.values())
                    # Step 1: Generate URLs from queries
                    st.info(f"📊 Generating URLs from {len(queries_list)} queries...")
                    urls_result = generate_urls(project['id'], queries_list)
                    
                    if urls_result.get('success'):
                        urls_info = urls_result.get('urls_result', {})
                        st.success(f"✅ Generated {urls_info.get('urls_added', 0)} URLs from {urls_info.get('queries_processed', 0)} search queries")
                        
                        # Step 2: Extract leads from URLs
                        st.info("🤖 Extracting leads from URLs (this may take several minutes)...")
                        leads_result = generate_leads(project['id'])
                        
                        if leads_result.get('success'):
                            # update project stats
                            project = get_project(project['id'])
                                
                            st.success("✅ Leads extracted successfully!")

                            st.markdown("**📊 Search Results (This Run):**")
                                
                            # Show stats from this run only (5-column dashboard)
                            col1, col2, col3, col4, col5 = st.columns(5)
                            with col1:
                                st.metric("Queries Processed", queries_processed)
                            with col2:
                                st.metric("Leads Processed", leads_result.get('new_leads_extracted', 0))
                            with col3:
                                st.metric("URLs Processed", leads_result.get('urls_processed', 0))
                            with col4:
                                st.metric("URLs Skipped", leads_result.get('urls_skipped', 0))
                            with col5:
                                st.metric("URLs Failed", leads_result.get('urls_failed', 0))
                            
                            st.info("📝 For detailed statistics, check the backend logs.")
                            # Automatically fetch ZIP file after successful extraction
                            with st.spinner("📥 Preparing download..."):
                                fetch_and_store_zip_data(project['id'])
                        else:
                            st.error(f"❌ Failed to generate leads")
                    else:
                        st.error(f"❌ Failed to generate URLs")
            else:
                st.error("❌ Please add at least one query before starting the search.")
    
    # Always show download section at the bottom of Web Search tab
    st.markdown("---")
    st.markdown("### 📥 Download Webscraped Leads")
    
    # Check if project has processed data
    has_data = project.get('leads_collected', 0) > 0
    
    if has_data:
        # Check if ZIP data is already in session state
        has_csv_data = "csv_data_all" in st.session_state
        
        if not has_csv_data:
            # Show button to load downloads
            if st.button("📥 Load Downloads", help="Fetch ZIP file from the latest run"):
                with st.spinner("📥 Loading downloads..."):
                    fetch_and_store_zip_data(project['id'])
                    st.rerun()
        
        # Show single ZIP download button if data is available
        if f"csv_data_all" in st.session_state:
            st.download_button(
                label="📦 Download All Results (ZIP)",
                data=st.session_state["csv_data_all"],
                file_name=st.session_state.get("csv_filename_all"),
                mime="application/zip",
                key="dl_all",
                use_container_width=True
            )
        else:
            st.info("📥 Click 'Load Downloads' above to prepare the download file.")
    else:
        st.info("ℹ️ No data available yet. Run a web search to generate downloadable CSV files.")

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
        
        # Preview data to help identify columns
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)
            
            st.markdown("#### 📊 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            st.info(f"📋 Found {len(df.columns)} columns: {', '.join(df.columns)}")
            
            # Upload form
            st.markdown("#### ⚙️ Dataset Configuration")
            
            with st.form("upload_dataset_form", clear_on_submit=False):
                dataset_name = st.text_input(
                    "Dataset Name",
                    value=uploaded_file.name.replace('.csv', ''),
                    help="Give your dataset a descriptive name"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    lead_column = st.selectbox(
                        "Lead Column",
                        options=df.columns.tolist(),
                        help="Select the column containing company names/leads"
                    )
                
                with col2:
                    enrichment_column = st.text_input(
                        "Enrichment Column Name",
                        value="enriched",
                        help="Name of the column for enrichment status (will be created if it doesn't exist)"
                    )
                
                enrichment_column_exists = st.checkbox(
                    "Enrichment column already exists in CSV",
                    value=False,
                    help="Check this if the enrichment column already exists in your CSV file"
                )
                
                submitted = st.form_submit_button("📤 Upload Dataset", type="primary")
                
                if submitted:
                    if not dataset_name or not dataset_name.strip():
                        st.error("❌ Please provide a dataset name")
                    elif not lead_column:
                        st.error("❌ Please select a lead column")
                    elif not enrichment_column or not enrichment_column.strip():
                        st.error("❌ Please provide an enrichment column name")
                    else:
                        with st.spinner("📤 Uploading dataset..."):
                            try:
                                result = upload_dataset(
                                    project_id=project['id'],
                                    dataset_name=dataset_name.strip(),
                                    lead_column=lead_column,
                                    enrichment_column=enrichment_column.strip(),
                                    enrichment_column_exists=enrichment_column_exists,
                                    csv_file=uploaded_file
                                )
                                
                                if result and result.get('success'):
                                    # Show success message immediately
                                    st.success(f"✅ {result.get('message', 'Dataset uploaded successfully')}")
                                    st.info(f"📊 Processed {result.get('rows_processed', 0)} rows")
                                    
                                    # Refresh project data to show updated stats
                                    project = get_project(project['id'])
                                else:
                                    st.error("❌ Failed to upload dataset. Please try again.")
                            except Exception as e:
                                st.error(f"❌ Error uploading dataset: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please make sure your file is a valid CSV file.")
    
    # Always show download section at the bottom of Upload Dataset tab
    st.markdown("---")
    st.markdown("### 📥 Download Dataset Data")
    
    # Check if project has dataset data
    has_dataset_data = project.get('datasets_added', 0) > 0
    
    if has_dataset_data:
        # Check if ZIP data is already in session state
        has_datasets_zip = "datasets_zip_data" in st.session_state
        
        if not has_datasets_zip:
            # Show button to load downloads
            if st.button("📥 Load Dataset Downloads", help="Fetch ZIP file with all dataset data", key="load_datasets_zip"):
                with st.spinner("📥 Loading dataset downloads..."):
                    fetch_and_store_datasets_zip(project['id'])
                    st.rerun()
        
        # Show single ZIP download button if data is available
        if "datasets_zip_data" in st.session_state:
            st.download_button(
                label="📦 Download All Dataset Data (ZIP)",
                data=st.session_state["datasets_zip_data"],
                file_name=st.session_state.get("datasets_zip_filename"),
                mime="application/zip",
                key="dl_datasets",
                use_container_width=True
            )
        else:
            st.info("📥 Click 'Load Dataset Downloads' above to prepare the download file.")
    else:
        st.info("ℹ️ No dataset data available yet. Upload a dataset above to generate downloadable CSV files.")
