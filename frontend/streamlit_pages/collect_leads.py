"""
Lead collection page
"""
import streamlit as st
import pandas as pd
from utils.display_errors import call_api
from api import (
    update_project,
    generate_queries,
    get_queries,
    generate_urls,
    get_urls,
    create_url,
    update_url,
    delete_url,
    generate_leads,
    fetch_latest_run_zip,
    get_project,
    upload_dataset,
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _fetch_and_store_zip_data(project_id: int):
    """Fetch ZIP file from API and store in session state"""
    result = call_api(fetch_latest_run_zip, project_id)
    if result:
        zip_content, filename = result
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
    st.markdown(f"# Lead Collection Tools - {project['project_name']}")
        
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
    current_project_id = st.session_state.selected_project.get('id') if st.session_state.selected_project else None

    if 'generated_queries' not in st.session_state:
        st.session_state.generated_queries = {}
    if current_project_id and current_project_id not in st.session_state.generated_queries:
        st.session_state.generated_queries[current_project_id] = {}
    if 'query_counter' not in st.session_state:
        st.session_state.query_counter = 0
    if 'num_queries' not in st.session_state:
        st.session_state.num_queries = 3
    if 'urls_table_just_saved' not in st.session_state:
        st.session_state.urls_table_just_saved = False
    if 'urls_table_save_message' not in st.session_state:
        st.session_state.urls_table_save_message = None
    if 'query_message' not in st.session_state:
        st.session_state.query_message = {}
    if current_project_id and current_project_id not in st.session_state.query_message:
        st.session_state.query_message[current_project_id] = None
    if 'criteria_message' not in st.session_state:
        st.session_state.criteria_message = {}
    if current_project_id and current_project_id not in st.session_state.criteria_message:
        st.session_state.criteria_message[current_project_id] = None
    if 'extraction_results' not in st.session_state:
        st.session_state.extraction_results = {}
    if current_project_id and current_project_id not in st.session_state.extraction_results:
        st.session_state.extraction_results[current_project_id] = {}  # Store full result dict from backend
    if 'generate_urls_running' not in st.session_state:
        st.session_state.generate_urls_running = {}
    if current_project_id and current_project_id not in st.session_state.generate_urls_running:
        st.session_state.generate_urls_running[current_project_id] = False
    if 'extract_leads_running' not in st.session_state:
        st.session_state.extract_leads_running = {}
    if current_project_id and current_project_id not in st.session_state.extract_leads_running:
        st.session_state.extract_leads_running[current_project_id] = False

# =============================================================================
# MAIN PAGE - WEB SEARCH TAB
# =============================================================================

def show_web_search_tab(project):
    """Web search tab content"""
    # Initialize page-specific session state
    project_id = project['id']
    init_collect_leads_session_state()

    # Ensure project_id key exists in generated_queries
    if project_id not in st.session_state.generated_queries:
        st.session_state.generated_queries[project_id] = {}
    
    # Get queries for current project
    project_queries = st.session_state.generated_queries[project_id]
    
    # Get query message for current project
    project_query_message = st.session_state.query_message.get(project_id)
    
    # Get criteria message for current project
    project_criteria_message = st.session_state.criteria_message.get(project_id)
    
    # Step 1: Search Queries
    st.markdown("## Step 1: Search Queries")
    
    # Main feature: Add search queries (always visible)
    st.markdown("**Add your own search queries:**")
    # Use a form to handle input clearing properly
    with st.form("add_query_form", clear_on_submit=True):
        new_query = st.text_input("Add custom query", placeholder="Enter your own search query...", key="new_query_input")
        submitted = st.form_submit_button("➕ Add Query")
        
        if submitted:
            if not new_query or not new_query.strip():
                st.error("❌ Please provide a query")
            else:
                # Check if query already exists for this project (case-insensitive)
                existing_queries = {q.lower().strip() for q in st.session_state.generated_queries.get(project_id, {}).values()}
                normalized_new_query = new_query.strip().lower()
                
                if normalized_new_query in existing_queries:
                    # Store message in session state so it persists after rerun
                    st.session_state.query_message[project_id] = f'⚠️ The query "{new_query.strip()}" is already present in the list.'
                    st.rerun()
                else:
                    # Clear extraction results when adding a new query
                    st.session_state.extraction_results[project_id] = {}
                    # Store success message
                    st.session_state.query_message[project_id] = f'✅ Added query "{new_query.strip()}" to the list.'
                    
                    query_id = f"q{st.session_state.query_counter}"
                    st.session_state.query_counter += 1
                    st.session_state.generated_queries[project_id][query_id] = new_query.strip()
                    st.rerun()
    
    # Optional feature: Generate AI queries (collapsible/expandable)
    with st.expander("🤖 Generate AI queries (Optional)", expanded=False):
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
                    "Edit query search target",
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
                            result = call_api(update_project, project['id'], query_search_target=updated_target.strip())
                            if result:
                                st.session_state.selected_project = result
                            else:
                                st.error("❌ Failed to save Query Search Target")
                                st.stop()
                    
                    # Clear extraction results when generating new queries
                    st.session_state.extraction_results[project_id] = {}
                    
                    # Generate queries
                    with st.spinner(f"🤖 AI is generating {st.session_state.num_queries} targeted search queries..."):
                        # Clear previous message when generating new queries
                        st.session_state.query_message[project_id] = None
                        
                        generated_queries = call_api(generate_queries, project['id'], num_queries=st.session_state.num_queries)
                        if generated_queries:
                            # Get existing queries for this project (case-insensitive comparison)
                            existing_queries = {q.lower().strip() for q in st.session_state.generated_queries.get(project_id, {}).values()}
                            
                            # Assign unique IDs to all new AI queries, skipping duplicates
                            added_count = 0
                            skipped_queries = []
                            for query in generated_queries:
                                normalized_query = query.lower().strip()
                                if normalized_query not in existing_queries:
                                    query_id = f"q{st.session_state.query_counter}"
                                    st.session_state.query_counter += 1
                                    st.session_state.generated_queries[project_id][query_id] = query
                                    existing_queries.add(normalized_query)  # Add to set to prevent duplicates in same batch
                                    added_count += 1
                                else:
                                    skipped_queries.append(query)
                            
                            # Store message in session state so it persists after rerun
                            if added_count > 0:
                                if skipped_queries:
                                    skipped_list = ', '.join([f'"{q}"' for q in skipped_queries])
                                    st.session_state.query_message[project_id] = f"⚠️ Added {added_count} new queries. Skipped {len(skipped_queries)} duplicate(s): {skipped_list}"
                                else:
                                    st.session_state.query_message[project_id] = f"✅ Generated {added_count} search queries!"
                            else:
                                st.session_state.query_message[project_id] = f"⚠️ All {len(generated_queries)} generated queries are already present in the list."
                            st.rerun()
                        else:
                            st.session_state.query_message[project_id] = "❌ Failed to generate queries. Please try again."
                            st.rerun()
    
    # Display all queries from database (always visible)
    st.markdown("**Previously run queries:**")
    db_queries = call_api(get_queries, project['id'])
    if db_queries and len(db_queries) > 0:
        # Create DataFrame for display
        queries_df = pd.DataFrame(db_queries)
        # Format date_added column for better readability
        if 'date_added' in queries_df.columns:
            queries_df['date_added'] = pd.to_datetime(queries_df['date_added']).dt.strftime('%Y-%m-%d %H:%M:%S')
        # Display only query and date_added columns
        display_df = queries_df[['query', 'date_added']].copy()
        display_df.columns = ['Query', 'Date Added']
        st.dataframe(display_df, width='stretch', hide_index=True)
    else:
        st.info("No queries have been run yet for this project.")
    
    # Display query messages if they exist (persists after rerun)
    if project_query_message:
        st.info(project_query_message)

    # Display and edit queries (always show if queries exist for this project)
    # Check session state directly to ensure we have the latest
    current_queries = st.session_state.generated_queries.get(project_id, {})
    if current_queries:
        st.markdown("**Your search queries:**")
        
        queries_to_delete = []
        queries_list = list(current_queries.items())  # Convert to list for display order
        
        for i, (query_id, query) in enumerate(queries_list):
            query_key = f"query_{project_id}_{query_id}"
            delete_key = f"remove_{project_id}_{query_id}"
            
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
                        st.session_state.generated_queries[project_id][query_id] = edited_query.strip()
                    else:  # Empty - mark for deletion
                        queries_to_delete.append(query_id)
            with col2:
                if st.button("❌", key=delete_key):
                    queries_to_delete.append(query_id)
        
        # Delete marked queries (simple - just remove from dict!)
        if queries_to_delete:
            for query_id in queries_to_delete:
                st.session_state.generated_queries[project_id].pop(query_id, None)
            # Clear message when queries are deleted
            st.session_state.query_message[project_id] = None
            st.rerun()

    # Step 2: Generate URLs (always visible)
    st.markdown("---")
    st.markdown("## Step 2: Validate URLs")
    
    # Get current project values for lead features (use latest from session state)
    current_project = st.session_state.selected_project

    # Check if queries exist for this project
    has_queries = bool(st.session_state.generated_queries.get(project_id, {}))
    
    # Initialize running state for this project
    generate_urls_running = st.session_state.generate_urls_running.get(project_id, False)
    
    # Show warning message if generating URLs
    if generate_urls_running:
        st.warning("⚠️ Please do not navigate away from this page (in-app) as progress will be lost.")
    
    if not has_queries:
        st.info("ℹ️ Add at least one search query in Step 1 before you can generate URLs.")
        st.button("🔍 Generate URLs", disabled=True)
    else:
        if st.button("🔍 Generate URLs", disabled=generate_urls_running):
            st.session_state.generate_urls_running[project_id] = True
            st.rerun()
    
    # Run URL generation if flag is set
    if generate_urls_running:
        # Clear previous save message when generating new URLs
        if 'urls_table_save_message' in st.session_state:
            st.session_state.urls_table_save_message = None
        
        with st.spinner("🔍 Generating URLs from queries..."):
            # Convert dict to list for API call (use queries for this project)
            queries_list = list(st.session_state.generated_queries.get(project_id, {}).values())
            urls_result = call_api(generate_urls, project['id'], queries_list)
            # Reset running state regardless of success or failure
            st.session_state.generate_urls_running[project_id] = False
            
            if urls_result:
                st.success(f"✅ Generated {urls_result.get('urls_added', 0)} URLs from {urls_result.get('queries_processed', 0)} search queries")
            else:
                st.error(f"❌ Failed to generate URLs")
            st.rerun()
    
    # Fetch and display URLs from backend
    urls = call_api(get_urls, project['id'])
    if not urls:
        urls = []
    
    # Display URLs table if they exist
    if urls:
        st.markdown("Based on your search queries, these are your generated URLs.")
        
        # Create DataFrame from URLs
        df = pd.DataFrame([
            {
                'ID': url['id'],
                'URL': url['link'],
                'Query': url.get('query', ''),
                'Title': url.get('title', ''),
                'Snippet': url.get('snippet', ''),
                'Date': url.get('date', ''),
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
            width='stretch',
            num_rows="dynamic",
            key=editor_key,
            column_config={
                "ID": None,
                "Query": st.column_config.TextColumn("Query"),
                "URL": st.column_config.TextColumn("URL", width="medium"),
                "Title": st.column_config.TextColumn("Title", width="medium"),
                "Snippet": st.column_config.TextColumn("Snippet", width="large"),
                "Date": st.column_config.TextColumn("Date", width="small"),
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
                            'snippet': str(row['Snippet']).strip() if pd.notna(row['Snippet']) else '',
                            'date': str(row['Date']).strip() if pd.notna(row.get('Date')) else None
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
                        
                        edited_date = normalize_for_compare(row.get('Date', ''))
                        original_date = normalize_for_compare(original_row.get('Date', ''))
                        if edited_date != original_date:
                            updates['date'] = edited_date if edited_date else None
                        
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
        # Only show if there are no pending changes (to avoid confusion)
        if st.session_state.urls_table_save_message and not has_changes:
            st.success(st.session_state.urls_table_save_message)
        
        if has_changes:
            if st.button("💾 Save Table"):
                # Process all changes
                changes_made = False
                
                # Create new rows
                for new_row in new_rows:
                    result = call_api(
                        create_url,
                        project['id'],
                        link=new_row['link'],
                        title=new_row['title'] if new_row['title'] else None,
                        snippet=new_row['snippet'] if new_row['snippet'] else None,
                        date=new_row['date'] if new_row.get('date') else None
                    )
                    if result:
                        changes_made = True
                
                # Update existing rows
                for url_id, updates in edited_rows:
                    result = call_api(update_url, project['id'], url_id, **updates)
                    if result:
                        changes_made = True
                
                # Delete removed rows
                for url_id in deleted_ids:
                    # Ensure url_id is a Python int
                    url_id_int = int(url_id)
                    result = call_api(delete_url, project['id'], url_id_int)
                    if result and result.get('success'):
                        changes_made = True
                
                # Show results
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
    
    # Bare minimum lead criteria editor (in Step 3)
    current_project = st.session_state.selected_project
    current_criteria = current_project.get('lead_minimum_criteria', '')
    
    st.markdown("**Bare Minimum Lead Criteria**: This is the most minimal/basic characteristic that a lead must have. Enter only the core type, not the full detailed criteria. Examples: For companies with sustainability initiatives → just 'company'. For pilling companies that have done gov contracts → just 'pilling company'. For doctors offices with 2+ people → just 'doctors office'.")

    with st.form("lead_criteria_form"):
        bare_minimum_criteria = st.text_input(
            "Edit the bare minimum lead criteria",
            value=current_criteria,
            placeholder="e.g. pilling company, doctors office, company",
            help="Enter the most basic/minimal characteristic. The AI will extract leads that meet this minimum, even if they have additional qualities.",
            key=f"bare_minimum_criteria_input_{project_id}"
        )
        
        criteria_submitted = st.form_submit_button("💾 Save Criteria", width='stretch')
        
        if criteria_submitted:
            # Clear previous message when submitting new criteria
            if st.session_state.criteria_message.get(project_id):
                st.session_state.criteria_message[project_id] = None
            
            # Validate that criteria is not empty
            if not bare_minimum_criteria or not bare_minimum_criteria.strip():
                st.error("❌ Bare Minimum Lead Criteria is required. Please enter criteria before saving.")
            else:
                # Save lead_minimum_criteria if it has changed
                if bare_minimum_criteria.strip() != current_criteria:
                    with st.spinner("Saving Bare Minimum Lead Criteria..."):
                        result = call_api(update_project, project['id'], lead_minimum_criteria=bare_minimum_criteria.strip())
                        if result:
                            st.session_state.selected_project = result
                            current_criteria = result.get('lead_minimum_criteria', '')
                            # Store success message in session state
                            st.session_state.criteria_message[project_id] = "✅ Bare Minimum Lead Criteria saved!"
                            st.rerun()
                        else:
                            st.error("❌ Failed to save Bare Minimum Lead Criteria")
    
    # Display criteria message if it exists (persists after rerun)
    if project_criteria_message:
        st.success(project_criteria_message)
    
    # Update current_criteria after potential save
    current_project = st.session_state.selected_project
    current_criteria = current_project.get('lead_minimum_criteria', '')
    
    # Validate both criteria and URLs before allowing extraction
    has_criteria = current_criteria and current_criteria.strip()
    has_urls = len(urls) > 0
    
    # Initialize running state for this project
    extract_leads_running = st.session_state.extract_leads_running.get(project_id, False)
    
    # Show warning message if extracting leads
    if extract_leads_running:
        st.warning("⚠️ Please do not navigate away from this page (in-app) as progress will be lost.")
    
    if not has_urls:
        st.info("ℹ️ Generate URLs in Step 2 before you can extract leads.")
        st.button("🤖 Extract Leads", disabled=True)
    elif not has_criteria:
        st.info("ℹ️ Please set Bare Minimum Lead Criteria above before extracting leads.")
        st.button("🤖 Extract Leads", disabled=True)
    else:
        # Get extraction results for current project
        project_extraction_result = st.session_state.extraction_results.get(project_id, {})
        
        # Show button - "Re-run Extraction" if results exist, otherwise "Extract Leads"
        button_text = "🔄 Re-run Extraction" if project_extraction_result else "🤖 Extract Leads"
        if st.button(button_text, disabled=extract_leads_running):
            st.session_state.extract_leads_running[project_id] = True
            st.rerun()
    
    # Run extraction if flag is set
    if extract_leads_running:
        # Clear previous results and queries when starting new extraction
        st.session_state.extraction_results[project_id] = {}
        st.session_state.generated_queries[project_id] = {}
        st.session_state.query_counter = 0
        st.session_state.query_message[project_id] = None
        st.session_state.criteria_message[project_id] = None
        
        with st.spinner("🤖 Extracting leads from URLs (this may take several minutes)..."):
            leads_result = call_api(generate_leads, project['id'])
            # Reset running state regardless of success or failure
            st.session_state.extract_leads_running[project_id] = False
            
            if leads_result:
                # Store full result (including stats from backend) in session state for this project
                st.session_state.extraction_results[project_id] = leads_result
                
                # Refresh project data to get updated stats
                updated_project = call_api(get_project, project['id'])
                if updated_project:
                    st.session_state.selected_project = updated_project
                
                # Automatically fetch ZIP file after successful extraction
                with st.spinner("📥 Preparing download..."):
                    _fetch_and_store_zip_data(project['id'])
            
            st.rerun()
    
    # Display extraction results if they exist for this project
    project_extraction_result = st.session_state.extraction_results.get(project_id, {})
    if project_extraction_result:
        st.markdown("---")
        st.markdown("## 📊 Extraction Results")
        
        # Use stats calculated by backend instead of recalculating
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Leads Extracted", project_extraction_result.get('new_leads_extracted', 0))
        with col2:
            st.metric("URLs Processed", project_extraction_result.get('urls_processed', 0))
        with col3:
            st.metric("URLs Skipped", project_extraction_result.get('urls_skipped', 0))
        with col4:
            st.metric("URLs Failed", project_extraction_result.get('urls_failed', 0))
        with col5:
            st.metric("Total URLs", project_extraction_result.get('total_urls_attempted', 0))
        
        # Prepare data for summary table from extracted_leads
        extracted_leads_list = project_extraction_result.get('extracted_leads', [])
        results_data = []
        for result in extracted_leads_list:
            leads = result.get('leads', [])
            status = result.get('status', 'unknown')
            # Color code status
            status_display = {
                'processed': '✅ Processed',
                'skip': '⏭️ Skipped',
                'failed': '❌ Failed',
                'unprocessed': '⏳ Unprocessed'
            }.get(status, status)
            
            results_data.append({
                'Status': status_display,
                'Query': result.get('query', 'N/A'),
                'URL': result['url'][:60] + '...' if len(result['url']) > 60 else result['url'],
                'Leads Found': len(leads),
                'Leads': ', '.join(leads[:5]) + ('...' if len(leads) > 5 else '') if leads else 'None'
            })
        
        df = pd.DataFrame(results_data)
        st.dataframe(df, width='stretch', hide_index=True)

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
                width='stretch'
            )
            # Note: st.download_button does NOT cause a rerun - it just triggers the download
        elif not has_csv_data:
            st.info("📥 Click 'Load Downloads' above to prepare the download file.")
    else:
        st.info("ℹ️ No data available yet. Run a web search to generate downloadable CSV files.")
        
def show_upload_dataset_tab(project):
    """Upload dataset tab content"""
    st.markdown("#### 📁 Upload Existing Dataset")

    # Show persistent success message
    upload_success_key = f"upload_success_{project['id']}"

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a CSV or Excel file with company data. Excel files with multiple sheets will be merged automatically.",
        key=f"dataset_upload_{project['id']}"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Determine file type
        is_excel = uploaded_file.name.lower().endswith(('.xlsx', '.xls'))
        is_csv = uploaded_file.name.lower().endswith('.csv')
        
        # Preview data to help identify columns
        try:
            uploaded_file.seek(0)
            
            # Initialize variables for column collection
            all_columns_set = None
            excel_file = None
            
            if is_excel:
                # Read Excel file - merge all sheets first
                excel_file = pd.ExcelFile(uploaded_file)
                uploaded_file.seek(0)
                
                if len(excel_file.sheet_names) > 1:
                    st.info(f"📊 Excel file detected with {len(excel_file.sheet_names)} sheet(s): {', '.join(excel_file.sheet_names)}")
                    st.info("ℹ️ Merging all sheets into one preview below. You'll select the lead column next.")
                else:
                    st.info(f"📊 Excel file detected with 1 sheet: {excel_file.sheet_names[0]}")
                
                # Merge all sheets for preview (concatenate vertically, column order based on Sheet 1)
                if len(excel_file.sheet_names) == 0:
                    df = pd.DataFrame()
                else:
                    # Read Sheet 1 first - this determines column order
                    sheet1_name = excel_file.sheet_names[0]
                    # Read with no row limit to ensure we get all rows
                    df_sheet1 = pd.read_excel(excel_file, sheet_name=sheet1_name, header=0, engine='openpyxl')
                    df_sheet1.columns = df_sheet1.columns.str.strip()
                    
                    # Log initial row count before filtering
                    initial_sheet1_rows = len(df_sheet1)
                    st.info(f"📊 Sheet 1 '{sheet1_name}': Read {initial_sheet1_rows} rows from Excel file")
                    
                    # Only drop rows where ALL values are NaN (completely empty rows)
                    df_sheet1 = df_sheet1.dropna(how='all')
                    
                    sheet1_rows_after_filter = len(df_sheet1)
                    if initial_sheet1_rows != sheet1_rows_after_filter:
                        st.warning(f"⚠️ Sheet 1 '{sheet1_name}': Filtered out {initial_sheet1_rows - sheet1_rows_after_filter} completely empty rows")
                    
                    # Sheet 1 columns determine the order (preserve order)
                    sheet1_columns = df_sheet1.columns.tolist()
                    all_columns_set = set(sheet1_columns)
                    
                    # Read all other sheets and collect any new columns
                    other_sheets_data = []
                    for sheet_name in excel_file.sheet_names[1:]:
                        df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name, header=0, engine='openpyxl')
                        df_sheet.columns = df_sheet.columns.str.strip()
                        
                        initial_rows = len(df_sheet)
                        st.info(f"📊 Sheet '{sheet_name}': Read {initial_rows} rows from Excel file")
                        
                        df_sheet = df_sheet.dropna(how='all')
                        rows_after_filter = len(df_sheet)
                        
                        if initial_rows != rows_after_filter:
                            st.info(f"   Filtered out {initial_rows - rows_after_filter} completely empty rows")
                        
                        all_columns_set.update(df_sheet.columns)
                        other_sheets_data.append(df_sheet)
                    
                    # Determine final column order: Sheet 1 columns first, then any new columns from other sheets
                    new_columns = sorted([col for col in all_columns_set if col not in sheet1_columns])
                    final_column_order = sheet1_columns + new_columns
                    
                    # Prepare Sheet 1 with all columns
                    df_sheet1_final = df_sheet1.copy()
                    for col in new_columns:
                        if col not in df_sheet1_final.columns:
                            df_sheet1_final[col] = ''
                    df_sheet1_final = df_sheet1_final[final_column_order]
                    df_sheet1_final = df_sheet1_final.fillna('')
                    
                    # Prepare other sheets with all columns (in correct order)
                    all_sheets_data = [df_sheet1_final]
                    
                    for df_sheet in other_sheets_data:
                        # Ensure all columns exist in this sheet (fill missing with blank)
                        for col in final_column_order:
                            if col not in df_sheet.columns:
                                df_sheet[col] = ''
                        
                        # Reorder columns to match Sheet 1's order + new columns
                        df_sheet = df_sheet[final_column_order]
                        df_sheet = df_sheet.fillna('')
                        
                        all_sheets_data.append(df_sheet)
                    
                    # Concatenate all sheets vertically (no row merging)
                    df = pd.concat(all_sheets_data, ignore_index=True)
                
                df.columns = df.columns.str.strip()
                uploaded_file.seek(0)
                
                st.markdown("#### 📊 Merged Data Preview (All Sheets)")
                
                # Show detailed row counts
                total_rows = len(df)
                preview_rows = min(50, total_rows)  # Show up to 50 rows in preview
                
                st.success(f"✅ Merged {len(excel_file.sheet_names)} sheet(s) into {total_rows} total rows")
                if total_rows > preview_rows:
                    st.info(f"📋 Showing first {preview_rows} rows (scroll down in table to see more)")
                
                st.dataframe(df.head(preview_rows), width='stretch', height=400)
            else:
                # CSV file
                df = pd.read_csv(uploaded_file)
                uploaded_file.seek(0)
                df.columns = df.columns.str.strip()
                
                st.markdown("#### 📊 Data Preview")
                st.dataframe(df.head(10), width='stretch')
            
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
            
            # Remove file extension for default dataset name
            default_name = uploaded_file.name
            for ext in ['.csv', '.xlsx', '.xls']:
                if default_name.lower().endswith(ext):
                    default_name = default_name[:-len(ext)]
                    break
            
            dataset_name = st.text_input(
                "Dataset Name",
                value=default_name,
                help="Give your dataset a descriptive name",
                key=dataset_name_key
            )
            
            # Use columns from the merged/preview dataframe
            all_columns = df.columns.tolist()
            
            lead_column = st.selectbox(
                "Lead Column",
                options=all_columns,
                help="Select the column containing company names/leads (primary identifier - rows with the same value will be combined)",
                key=lead_column_key
            )
            
            # Check if there are any columns available for enrichment (excluding lead column)
            available_columns = [col for col in all_columns if col != lead_column]
            has_available_columns = len(available_columns) > 0
            
            # Checkbox to enable enrichment columns from dataset (outside form for immediate updates)
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = False
            
            add_enrichment_from_dataset = st.checkbox(
                "Add enrichment columns from dataset",
                value=st.session_state[checkbox_key],
                disabled=not has_available_columns,
                help="If checked, you can select columns from your file to use as enrichment columns. If unchecked, a single column named '{dataset_name}_exists' with all values TRUE will be created." + 
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
                        help="Select one or more columns from your file to use as enrichment columns. Each selected column will become a separate column in the merged results table.",
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
            if st.button("📤 Upload Dataset", type="primary", width='stretch', key=upload_button_key):
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
                        # Prepare enrichment columns data
                        if add_enrichment_from_dataset:
                            # Multiple enrichment columns from CSV - join with comma
                            enrichment_column_data = enrichment_columns
                            enrichment_column_exists = True
                        else:
                            # Single enrichment column - backend will generate {dataset_name}_exists
                            enrichment_column_data = None
                            enrichment_column_exists = False
                        
                        result = call_api(
                            upload_dataset,
                            project_id=project['id'],
                            dataset_name=dataset_name.strip(),
                            lead_column=lead_column,
                            enrichment_column_list=enrichment_column_data,
                            enrichment_column_exists=enrichment_column_exists,
                            file=uploaded_file
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
                            updated_project = call_api(get_project, project['id'])
                            if updated_project:
                                st.session_state.selected_project = updated_project
        except Exception as e:
            file_type = "Excel" if is_excel else "CSV"
            st.error(f"❌ Error reading {file_type} file: {str(e)}")
            st.info(f"Please make sure your file is a valid {file_type} file.")

        if upload_success_key in st.session_state:
            st.success(st.session_state[upload_success_key])