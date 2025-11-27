"""
Lead collection page
"""
import streamlit as st
import pandas as pd
from api_client import update_project, generate_queries, generate_urls, generate_leads, fetch_latest_run_zip, get_project, upload_dataset

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _fetch_and_store_zip_data(project_id: int):
    """Fetch ZIP file from API and store in session state"""
    zip_content, filename = fetch_latest_run_zip(project_id)
    if zip_content and filename:
        st.session_state["csv_data_all"] = zip_content
        st.session_state["csv_filename_all"] = filename
        return True
    return False


# =============================================================================
# MAIN PAGE
# =============================================================================

def show_collect_leads():
    """Lead collection page"""
    project = st.session_state.selected_project
    st.markdown(f"# Lead Collection Tools: {project['project_name']}")
        
    # Lead collection methods - 3 ways to collect leads
    tab1, tab2 = st.tabs(["🌐 AI Web Search", "📁 Upload Dataset"])
    
    with tab1:
        show_web_search_tab(project)
    
    with tab2:
        show_upload_dataset_tab(project)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_collect_leads_session_state():
    """Initialize session state variables for collect leads page"""
    if 'generated_queries' not in st.session_state:
        st.session_state.generated_queries = {}
    if 'query_counter' not in st.session_state:
        st.session_state.query_counter = 0
    if 'num_queries' not in st.session_state:
        st.session_state.num_queries = 3

# =============================================================================
# MAIN PAGE - WEB SEARCH TAB
# =============================================================================

def show_web_search_tab(project):
    """Web search tab content"""
    # Initialize page-specific session state
    init_collect_leads_session_state()
    
    # Step 1: Search Queries
    st.markdown("## Step 1: Search Queries")
    st.markdown("**Generate AI queries:**")
    
    # Query Search Target editor (required for AI generation)
    # Use latest project data from session state
    current_project = st.session_state.selected_project
    current_target = current_project.get('query_search_target', '')

    with st.form("generate_queries_form"):
        # Text area on left, number of queries on right
        col1, col2 = st.columns([3, 1])
        with col1:
            # Editable field
            updated_target = st.text_area(
                "Edit Query Search Target",
                value=current_target,
                placeholder="e.g., Find sustainable energy companies in California that are focused on solar and wind power...",
                height=100,
                help="Describe what you're looking for. This helps AI generate better search queries.",
                key="query_search_target_input"
            )

        with col2:
            num_queries = st.number_input(
                "Number of queries to generate",
                min_value=1,
                max_value=20,
                value=st.session_state.num_queries,
                step=1,
                help="How many AI-generated queries would you like? (1-20)",
                key="num_queries_input"
            )
            st.session_state.num_queries = num_queries

        # Generate button (form submit button)
        generate_submitted = st.form_submit_button(
            "🔍 Generate Smart Queries"
        )

        if generate_submitted:
            # Validate input
            if not updated_target or not updated_target.strip():
                st.error("❌ Query Search Target cannot be empty")
            else:
                # Save query_search_target if it has changed
                if updated_target.strip() != current_target:
                    with st.spinner("Saving Query Search Target..."):
                        result = update_project(project['id'], query_search_target=updated_target.strip())
                        if result:
                            st.session_state.selected_project = result
                        else:
                            st.error("❌ Failed to save Query Search Target")
                            st.stop()
                
                # Generate queries
                with st.spinner(f"🤖 AI is generating {st.session_state.num_queries} targeted search queries..."):
                    generated_queries = generate_queries(project['id'], num_queries=st.session_state.num_queries)
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

    st.markdown("**Or add your own search queries:**")
    # Use a form to handle input clearing properly
    with st.form("add_query_form", clear_on_submit=True):
        new_query = st.text_input("Add custom query", placeholder="Enter your own search query...", key="new_query_input")
        submitted = st.form_submit_button("➕ Add Query")
        if submitted and new_query and new_query.strip():
            query_id = f"q{st.session_state.query_counter}"
            st.session_state.query_counter += 1
            st.session_state.generated_queries[query_id] = new_query.strip()
            st.rerun()

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

    # Step 2: Start search (always visible)
    st.markdown("---")
    st.markdown("## Step 2: Start the search")
    
    # Test Prompts button at the top
    if st.button("🧪 Test Extraction Prompts", help="Test your lead features prompts before running the full extraction"):
        st.session_state.current_page = "test_prompts"
        st.rerun()
    
    # Get current project values for lead features (use latest from session state)
    current_project = st.session_state.selected_project
    current_lead_features_we_want = current_project.get('lead_features_we_want', '') or ''
    current_lead_features_to_avoid = current_project.get('lead_features_to_avoid', '') or ''
    
    # Lead features input boxes (read-only - edit in test prompts page)
    st.info("💡 To edit lead features, use the 'Test Extraction Prompts' button above or go to the Test Prompts page.")
    col1, col2 = st.columns(2)
    with col1:
        lead_features_we_want = st.text_area(
            "Lead Features We Want",
            value=current_lead_features_we_want,
            placeholder="e.g., Companies focused on sustainability, B2B SaaS companies, etc.",
            height=100,
            help="Describe the features or characteristics you want in your leads (edit in Test Prompts page)",
            key="lead_features_we_want_input",
            disabled=True
        )
    with col2:
        lead_features_to_avoid = st.text_area(
            "Lead Features to Avoid",
            value=current_lead_features_to_avoid,
            placeholder="e.g., Companies that sell to consumers, companies in specific industries, etc.",
            height=100,
            help="Describe the features or characteristics you want to avoid in your leads (edit in Test Prompts page)",
            key="lead_features_to_avoid_input",
            disabled=True
        )
    
    # Check if queries exist and lead features are set
    has_queries = bool(st.session_state.generated_queries)
    has_lead_features = bool(lead_features_we_want.strip())
    
    if not has_queries:
        st.info("ℹ️ Add at least one search query in Step 1 before you can start the web search.")
        st.button("🔍 Start Web Search", disabled=True)
    elif not has_lead_features:
        st.warning("⚠️ Please configure lead features before starting the web search. Use the 'Test Extraction Prompts' button above to set them.")
        st.button("🔍 Start Web Search", disabled=True)
    else:
        if st.button("🔍 Start Web Search"):
            # Save lead features if they have changed
            features_changed = (
                lead_features_we_want.strip() != current_lead_features_we_want or
                lead_features_to_avoid.strip() != current_lead_features_to_avoid
            )
            
            if features_changed:
                with st.spinner("💾 Saving lead features..."):
                    result = update_project(
                        project['id'],
                        lead_features_we_want=lead_features_we_want.strip() if lead_features_we_want.strip() else None,
                        lead_features_to_avoid=lead_features_to_avoid.strip() if lead_features_to_avoid.strip() else None
                    )
                    if result:
                        st.session_state.selected_project = result
                    else:
                        st.error("❌ Failed to save lead features")
                        st.stop()
            
            with st.spinner("🔍 Starting web search..."):
                # Convert dict to list for API call
                queries_list = list(st.session_state.generated_queries.values())
                # Step 2.1: Generate URLs from queries
                st.info(f"📊 Generating URLs from {len(queries_list)} queries...")
                urls_result = generate_urls(project['id'], queries_list)
                
                if urls_result.get('success'):
                    urls_info = urls_result.get('urls_result', {})
                    st.success(f"✅ Generated {urls_info.get('urls_added', 0)} URLs from {urls_info.get('queries_processed', 0)} search queries")
                    
                    # Step 2.2: Extract leads from URLs
                    st.info("🤖 Extracting leads from URLs (this may take several minutes)...")
                    leads_result = generate_leads(project['id'])
                    
                    if leads_result.get('success'):
                        st.success("✅ Leads extracted successfully!")
                        
                        # Refresh project data to get updated stats
                        st.session_state.selected_project = get_project(project['id'])

                        st.markdown("**📊 Search Results (This Run):**")

                        # Show stats from this run only (5-column dashboard)
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Queries Processed", urls_info.get('queries_processed', 0))
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
                            _fetch_and_store_zip_data(project['id'])
                        
                        # Clear queries after successful completion so they don't persist on page reset
                        if 'generated_queries' in st.session_state:
                            st.session_state.generated_queries = {}
                        if 'query_counter' in st.session_state:
                            st.session_state.query_counter = 0
                    else:
                        st.error(f"❌ Failed to generate leads")
                else:
                    st.error(f"❌ Failed to generate URLs")
    
    # Always show download section at the bottom of Web Search tab
    st.markdown("---")
    st.markdown("### 📥 Download Webscraped Leads")
    
    # Use fresh project data from session state (may have been updated during this run)
    project = st.session_state.selected_project
    has_data = project.get('leads_collected', 0) > 0
    
    if has_data:
        # Check if ZIP data is already in session state
        has_csv_data = "csv_data_all" in st.session_state and st.session_state.get("csv_data_all") is not None
        
        if not has_csv_data:
            # Show button to load downloads
            if st.button("📥 Load Downloads", help="Fetch ZIP file from the latest run"):
                with st.spinner("📥 Loading downloads..."):
                    if _fetch_and_store_zip_data(project['id']):
                        st.success("✅ Downloads ready! The download button will appear below.")
                        # Don't rerun - Streamlit will rerun automatically on button click anyway
                    else:
                        st.error("❌ Failed to load downloads. Please try again.")
        
        # Show single ZIP download button if data is available
        if has_csv_data:
            download_key = "dl_serp"
            st.download_button(
                label="📦 Download All Results (ZIP)",
                data=st.session_state["csv_data_all"],
                file_name=st.session_state.get("csv_filename_all", "serp_results.zip"),
                mime="application/zip",
                key=download_key,
                use_container_width=True
            )
            # Note: st.download_button does NOT cause a rerun - it just triggers the download
        elif not has_csv_data:
            st.info("📥 Click 'Load Downloads' above to prepare the download file.")
    else:
        st.info("ℹ️ No data available yet. Run a web search to generate downloadable CSV files.")

def show_upload_dataset_tab(project):
    """Upload dataset tab content"""
    st.markdown("#### 📁 Upload Existing Dataset")
    
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
                
                submitted = st.form_submit_button("📤 Upload Dataset")
                
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
    
