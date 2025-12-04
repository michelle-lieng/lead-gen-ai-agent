"""
Lead collection page
"""
import streamlit as st
import pandas as pd
from api_client import update_project, generate_queries, generate_urls, get_urls, create_url, update_url, delete_url, generate_leads, fetch_latest_run_zip, get_project, upload_dataset

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
    if 'urls_table_just_saved' not in st.session_state:
        st.session_state.urls_table_just_saved = False
    if 'urls_table_save_message' not in st.session_state:
        st.session_state.urls_table_save_message = None

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

    # Step 2: Generate URLs (always visible)
    st.markdown("---")
    st.markdown("## Step 2: Generate URLs")
    
    # Get current project values for lead features (use latest from session state)
    current_project = st.session_state.selected_project

    # Check if queries exist
    has_queries = bool(st.session_state.generated_queries)
    
    if not has_queries:
        st.info("ℹ️ Add at least one search query in Step 1 before you can generate URLs.")
        st.button("🔍 Generate URLs", disabled=True)
    else:
        if st.button("🔍 Generate URLs"):
            with st.spinner("🔍 Generating URLs from queries..."):
                # Convert dict to list for API call
                queries_list = list(st.session_state.generated_queries.values())
                urls_result = generate_urls(project['id'], queries_list)
                
                if urls_result.get('success'):
                    urls_info = urls_result.get('urls_result', {})
                    st.success(f"✅ Generated {urls_info.get('urls_added', 0)} URLs from {urls_info.get('queries_processed', 0)} search queries")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to generate URLs")
    
    # Fetch and display URLs from backend
    try:
        urls = get_urls(project['id'])
    except Exception as e:
        st.error(f"❌ Error fetching URLs: {str(e)}")
        urls = []
    
    # Display URLs table if they exist
    if urls:
        st.markdown("**Your generated URLs (you can add, edit and delete URLs below):**")
        
        # Create DataFrame from URLs
        df = pd.DataFrame([
            {
                'ID': url['id'],
                'URL': url['link'],
                'Query': url.get('query', ''),
                'Title': url.get('title', ''),
                'Snippet': url.get('snippet', ''),
                'Status': url.get('status', 'unprocessed')
            }
            for url in urls
        ])
        
        # Store original for comparison
        original_df = df.copy()
        
        # Use a key that changes after save to reset the widget state
        editor_key = f"urls_editor_{st.session_state.urls_table_just_saved}"
        
        # Display editable table
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            key=editor_key,
            column_config={
                "ID": None,
                "Query": st.column_config.TextColumn("Query"),
                "URL": st.column_config.TextColumn("URL", width="medium"),
                "Title": st.column_config.TextColumn("Title", width="medium"),
                "Snippet": st.column_config.TextColumn("Snippet", width="large"),
                "Status": None
            },
            disabled=["Query", "Status", "ID"],  # These are read only!
        )
        
        # Check for changes first - create lookup dict for O(1) access
        # CRITICAL FIX: Convert all IDs to Python ints to avoid numpy int64 vs Python int mismatch
        # original_df['ID'].values contains numpy int64, but edited_ids contains Python int
        # Set operations fail when types don't match: {36 (numpy int64)} - {36 (Python int)} = {36} ❌
        original_ids = {int(id_val) for id_val in original_df['ID'].values if pd.notna(id_val)}
        original_dict = {int(row['ID']): row for _, row in original_df.iterrows()}
        edited_ids = set()
        new_rows = []
        edited_rows = []
        
        # Process all rows in edited_df to detect changes
        if len(edited_df) > 0:
            for idx, row in edited_df.iterrows():
                # Check if ID is NaN or missing (new row)
                if pd.isna(row['ID']) or row['ID'] == '':
                    # New row - validate URL is provided (required)
                    if pd.notna(row['URL']) and str(row['URL']).strip():
                        new_rows.append({
                            'link': str(row['URL']).strip(),
                            'title': str(row['Title']).strip() if pd.notna(row['Title']) else '',
                            'snippet': str(row['Snippet']).strip() if pd.notna(row['Snippet']) else ''
                        })
                else:
                    # Existing row - track ID and check for changes
                    # Convert to Python int (handles both int and float from Streamlit)
                    url_id = int(float(row['ID']))  # int(float()) handles 36, 36.0, numpy types
                    edited_ids.add(url_id)
                    
                    if url_id in original_dict:
                        original_row = original_dict[url_id]
                        updates = {}
                        
                        # Normalize values for comparison (handle NaN, None, whitespace, data types)
                        def normalize_for_compare(val):
                            if pd.isna(val) or val is None:
                                return ''
                            return str(val).strip()
                        
                        # Only add to updates if values actually differ after normalization
                        edited_url = normalize_for_compare(row['URL'])
                        original_url = normalize_for_compare(original_row['URL'])
                        if edited_url != original_url:
                            if not edited_url:  # URL cannot be empty
                                st.error(f"❌ URL cannot be empty for row with ID {url_id}")
                            else:
                                updates['link'] = edited_url
                        
                        edited_title = normalize_for_compare(row['Title'])
                        original_title = normalize_for_compare(original_row['Title'])
                        if edited_title != original_title:
                            updates['title'] = edited_title
                        
                        edited_snippet = normalize_for_compare(row['Snippet'])
                        original_snippet = normalize_for_compare(original_row['Snippet'])
                        if edited_snippet != original_snippet:
                            updates['snippet'] = edited_snippet
                        
                        if updates:
                            edited_rows.append((url_id, updates))
        
        # Find deleted rows (in original but not in edited)
        deleted_ids = original_ids - edited_ids
        
        # Only show save button if there are changes
        has_changes = len(new_rows) > 0 or len(edited_rows) > 0 or len(deleted_ids) > 0
        
        # Clear save message if new changes are detected
        if has_changes and st.session_state.urls_table_save_message:
            st.session_state.urls_table_save_message = None
        
        # Display save message below the table if it exists (from previous save)
        if st.session_state.urls_table_save_message:
            st.success(st.session_state.urls_table_save_message)
        
        if has_changes:
            if st.button("💾 Save Table"):
                # Process all changes
                changes_made = False
                errors = []
                
                # Create new rows
                for new_row in new_rows:
                    try:
                        result = create_url(
                            project['id'],
                            link=new_row['link'],
                            title=new_row['title'] if new_row['title'] else None,
                            snippet=new_row['snippet'] if new_row['snippet'] else None
                        )
                        if result and result.get('success'):
                            changes_made = True
                    except Exception as e:
                        errors.append(f"Error creating URL {new_row['link']}: {str(e)}")
                
                # Update existing rows
                for url_id, updates in edited_rows:
                    try:
                        result = update_url(project['id'], url_id, **updates)
                        if result and result.get('success'):
                            changes_made = True
                    except Exception as e:
                        errors.append(f"Error updating URL {url_id}: {str(e)}")
                
                # Delete removed rows
                for url_id in deleted_ids:
                    try:
                        # Ensure url_id is a Python int
                        url_id_int = int(url_id)
                        result = delete_url(project['id'], url_id_int)
                        if result and result.get('success'):
                            changes_made = True
                    except Exception as e:
                        errors.append(f"Error deleting URL {url_id} (project {project['id']}): {str(e)}")
                
                # Show results
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                
                if changes_made:
                    summary = []
                    if new_rows:
                        summary.append(f"Created {len(new_rows)} URL(s)")
                    if edited_rows:
                        summary.append(f"Updated {len(edited_rows)} URL(s)")
                    if deleted_ids:
                        summary.append(f"Deleted {len(deleted_ids)} URL(s)")
                    # Store message in session state so it persists across rerun
                    st.session_state.urls_table_save_message = f"✅ Saved! {' | '.join(summary)}"
                    # Toggle the flag to change the data_editor key, forcing a reset
                    st.session_state.urls_table_just_saved = not st.session_state.urls_table_just_saved
                    st.rerun()
    elif has_queries:
        st.info("ℹ️ No URLs generated yet. Click 'Generate URLs' above to create URLs from your queries.")
    
    # Step 3: Extract Leads (only show if URLs exist)
    st.markdown("---")
    st.markdown("## Step 3: Extract Leads")
    
    if not urls:
        st.info("ℹ️ Generate URLs in Step 2 before you can extract leads.")
        st.button("🤖 Extract Leads", disabled=True)
    else:
        if st.button("🤖 Extract Leads"):
            with st.spinner("🤖 Extracting leads from URLs (this may take several minutes)..."):
                leads_result = generate_leads(project['id'])
                
                if leads_result.get('success'):
                    st.success("✅ Leads extracted successfully!")
                    
                    # Refresh project data to get updated stats
                    st.session_state.selected_project = get_project(project['id'])

                    st.markdown("**📊 Extraction Results:**")

                    # Show stats from this run only (5-column dashboard)
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Leads Processed", leads_result.get('new_leads_extracted', 0))
                    with col2:
                        st.metric("URLs Processed", leads_result.get('urls_processed', 0))
                    with col3:
                        st.metric("URLs Skipped", leads_result.get('urls_skipped', 0))
                    with col4:
                        st.metric("URLs Failed", leads_result.get('urls_failed', 0))
                    with col5:
                        st.metric("Total URLs", len(urls))
                    
                    st.info("📝 For detailed statistics, check the backend logs.")
                    # Automatically fetch ZIP file after successful extraction
                    with st.spinner("📥 Preparing download..."):
                        _fetch_and_store_zip_data(project['id'])
                    
                    # Clear queries after successful completion so they don't persist on page reset
                    if 'generated_queries' in st.session_state:
                        st.session_state.generated_queries = {}
                    if 'query_counter' in st.session_state:
                        st.session_state.query_counter = 0
                    
                    st.rerun()
                else:
                    st.error(f"❌ Failed to extract leads")
    
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

    # Test Prompts button at the top
    if st.button("🧪 Test Extraction Prompts", help="Test your lead features prompts before running the full extraction"):
        st.session_state.current_page = "test_prompts"
        st.rerun()
        
    # Lead features input boxes (read-only - edit in test prompts page)
    st.info("💡 To edit lead features, use the 'Test Extraction Prompts' button above or go to the Test Prompts page.")

def show_upload_dataset_tab(project):
    """Upload dataset tab content"""
    st.markdown("#### 📁 Upload Existing Dataset")

    # Show persistent success message
    upload_success_key = f"upload_success_{project['id']}"

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file with company data",
        key=f"dataset_upload_{project['id']}"
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
            
            # Configuration section (outside form for dynamic updates)
            dataset_name_key = f"dataset_name_{project['id']}_{uploaded_file.name}"
            lead_column_key = f"lead_column_{project['id']}_{uploaded_file.name}"
            checkbox_key = f"add_enrichment_{project['id']}_{uploaded_file.name}"
            enrichment_columns_key = f"enrichment_columns_{project['id']}_{uploaded_file.name}"
            
            # Track previous form state to detect changes
            form_state_key = f"form_state_{project['id']}_{uploaded_file.name}"
            previous_state = st.session_state.get(form_state_key, {})
            
            dataset_name = st.text_input(
                "Dataset Name",
                value=uploaded_file.name.replace('.csv', ''),
                help="Give your dataset a descriptive name",
                key=dataset_name_key
            )
            
            lead_column = st.selectbox(
                "Lead Column",
                options=df.columns.tolist(),
                help="Select the column containing company names/leads",
                key=lead_column_key
            )
            
            # Check if there are any columns available for enrichment (excluding lead column)
            available_columns = [col for col in df.columns.tolist() if col != lead_column]
            has_available_columns = len(available_columns) > 0
            
            # Checkbox to enable enrichment columns from dataset (outside form for immediate updates)
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = False
            
            add_enrichment_from_dataset = st.checkbox(
                "Add enrichment columns from dataset",
                value=st.session_state[checkbox_key],
                disabled=not has_available_columns,
                help="If checked, you can select columns from your CSV to use as enrichment columns. If unchecked, a single column named '{dataset_name}_exists' with all values TRUE will be created." + 
                     (" ⚠️ No other columns available (only lead column found)." if not has_available_columns else ""),
                key=checkbox_key
            )
            
            # Store selected enrichment columns in session state
            if add_enrichment_from_dataset:
                # Show multi-select for enrichment columns
                if available_columns:
                    # Get previously selected columns from session state
                    default_selection = st.session_state.get(enrichment_columns_key, [])
                    
                    enrichment_columns = st.multiselect(
                        "Select Enrichment Columns",
                        options=available_columns,
                        default=default_selection,
                        help="Select one or more columns from your CSV to use as enrichment columns. Each selected column will become a separate column in the merged results table.",
                        key=enrichment_columns_key
                    )
                                        
                    if enrichment_columns:
                        st.success(f"✅ {len(enrichment_columns)} column(s) selected: {', '.join(enrichment_columns)}")
                    else:
                        st.warning("⚠️ Please select at least one enrichment column")
                else:
                    enrichment_columns = []
            else:
                # Single column will be created: {dataset_name}_exists with all TRUE values
                safe_dataset_name = dataset_name.strip().lower().replace(' ', '_')
                st.info(f"ℹ️ A single enrichment column named `{safe_dataset_name}_exists` will be created with all values set to TRUE")
                enrichment_columns = None
                # Clear session state when checkbox is unchecked
                if enrichment_columns_key in st.session_state:
                    del st.session_state[enrichment_columns_key]
            
            # Check if any form value changed and clear success message
            current_state = {
                'dataset_name': st.session_state.get(dataset_name_key),
                'lead_column': st.session_state.get(lead_column_key),
                'add_enrichment': st.session_state.get(checkbox_key, False),
                'enrichment_columns': tuple(sorted(st.session_state.get(enrichment_columns_key, []))) if st.session_state.get(checkbox_key) else None
            }
            
            if previous_state and previous_state != current_state:
                # Form values changed - clear success message
                if upload_success_key in st.session_state:
                    del st.session_state[upload_success_key]
            
            # Store current state for next comparison
            st.session_state[form_state_key] = current_state
            
            st.markdown("---")
            
            # Upload button (outside form)
            upload_button_key = f"upload_btn_{project['id']}_{uploaded_file.name}"
            if st.button("📤 Upload Dataset", type="primary", use_container_width=True, key=upload_button_key):
                # Clear previous success message when starting a new upload
                if upload_success_key in st.session_state:
                    del st.session_state[upload_success_key]
                
                # Validation
                if not dataset_name or not dataset_name.strip():
                    st.error("❌ Please provide a dataset name")
                elif not lead_column:
                    st.error("❌ Please select a lead column")
                elif add_enrichment_from_dataset and not enrichment_columns:
                    st.error("❌ Please select at least one enrichment column")
                else:
                    with st.spinner("📤 Uploading dataset..."):
                        try:
                            # Prepare enrichment columns data
                            if add_enrichment_from_dataset:
                                # Multiple enrichment columns from CSV - join with comma
                                enrichment_column_data = enrichment_columns
                                enrichment_column_exists = True
                            else:
                                # Single enrichment column - backend will generate {dataset_name}_exists
                                enrichment_column_data = None
                                enrichment_column_exists = False
                            
                            result = upload_dataset(
                                project_id=project['id'],
                                dataset_name=dataset_name.strip(),
                                lead_column=lead_column,
                                enrichment_column_list=enrichment_column_data,
                                enrichment_column_exists=enrichment_column_exists,
                                csv_file=uploaded_file
                            )
                            
                            if result and result.get('success'):
                                # Store success message in session state to persist
                                success_message = f"✅ {result.get('message', 'Dataset uploaded successfully')}"
                                st.session_state[upload_success_key] = success_message
                                                                
                                # Clear form-related session state after successful upload
                                if checkbox_key in st.session_state:
                                    del st.session_state[checkbox_key]
                                if enrichment_columns_key in st.session_state:
                                    del st.session_state[enrichment_columns_key]
                                
                                # Refresh project data in session state to show updated stats
                                updated_project = get_project(project['id'])
                                if updated_project:
                                    st.session_state.selected_project = get_project(project['id'])
                            else:
                                st.error("❌ Failed to upload dataset. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error uploading dataset: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please make sure your file is a valid CSV file.")

        if upload_success_key in st.session_state:
            st.success(st.session_state[upload_success_key])

