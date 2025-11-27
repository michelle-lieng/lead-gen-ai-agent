"""
Test extraction prompts page
"""
import streamlit as st
import pandas as pd
from api_client import (
    update_project, get_project, 
    generate_test_urls, get_test_urls, create_test_url, update_test_url, delete_test_url, extract_test_leads
)

def init_test_prompts_session_state():
    """Initialize session state variables for test prompts page"""
    if 'test_results' not in st.session_state:
        st.session_state.test_results = []  # List of dicts: {url, query, title, snippet, extracted_companies, status}
    if 'table_just_saved' not in st.session_state:
        st.session_state.table_just_saved = False  # Flag to track if table was just saved (used for widget key reset)
    if 'table_save_message' not in st.session_state:
        st.session_state.table_save_message = None  # Message to display after save (persists across rerun)

def show_test_prompts():
    """Test extraction prompts page"""
    project = st.session_state.selected_project
    if not project:
        st.error("No project selected")
        return
    
    # Initialize session state
    init_test_prompts_session_state()
    
    # Get fresh project data
    project = get_project(project['id'])
    if project:
        st.session_state.selected_project = project
    
    st.markdown(f"# Test Extraction Prompts: {project['project_name']}")
    
    # Back button
    if st.button("← Back to Lead Collection", type="secondary"):
        st.session_state.current_page = "collect_leads"
        st.rerun()
    
    st.markdown("---")
    
    # Section 1: Manage Test URLs
    st.markdown("## Step 1: Create Test URLs")

    # Generate URLs from Query
    st.markdown(f"Generate URLS from a search query to test lead extraction on:")
    with st.form("generate_urls_form", clear_on_submit=True):
        test_query_for_urls = st.text_input(
            "Search Query",
            placeholder="e.g., top sustainable companies in Australia",
            help="Enter a search query to generate URLs from"
        )
        generate_submitted = st.form_submit_button("🔍 Generate URLs")
        
        if generate_submitted and test_query_for_urls:
            with st.spinner("🔍 Generating URLs from query..."):
                try:
                    result = generate_test_urls(project['id'], test_query_for_urls)
                    if result and result.get('success'):
                        st.success(f"✅ {result.get('message', 'URLs generated successfully')}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to generate URLs")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Fetch and display test URLs from backend
    try:
        test_urls = get_test_urls(project['id'])
    except Exception as e:
        st.error(f"❌ Error fetching test URLs: {str(e)}")
        test_urls = []
    
    # Display test URLs as editable table with delete functionality
    if test_urls:
        st.markdown(f"Below you can add, edit and delete URLs:")
        
        # Create DataFrame from test URLs
        df = pd.DataFrame([
            {
                'ID': url['id'],
                'URL': url['link'],
                'Query': url.get('query', ''),
                'Title': url.get('title', ''),
                'Snippet': url.get('snippet', ''),
                'Status': url.get('status', 'unprocessed')
            }
            for url in test_urls
        ])
        
        # Store original for comparison
        original_df = df.copy()
        
        # Use a key that changes after save to reset the widget state
        # This prevents false positives after saving
        editor_key = f"test_urls_editor_{st.session_state.table_just_saved}"
        
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
            disabled=["Query"],  # These columns are read-only
        )
        
        # Check for changes first - create lookup dict for O(1) access
        original_ids = set(original_df['ID'].values)
        original_dict = {int(row['ID']): row for _, row in original_df.iterrows()}
        edited_ids = set()
        new_rows = []
        edited_rows = []
        
        # Process all rows in edited_df to detect changes
        if len(edited_df) > 0:
            for idx, row in edited_df.iterrows():
                # Check if ID is NaN or missing (new row)
                if pd.isna(row['ID']) or row['ID'] == '':
                    # New row - validate URL is provided
                    if pd.notna(row['URL']) and str(row['URL']).strip():
                        new_rows.append({
                            'link': str(row['URL']).strip(),
                            'title': str(row['Title']).strip() if pd.notna(row['Title']) else '',
                            'snippet': str(row['Snippet']).strip() if pd.notna(row['Snippet']) else ''
                        })
                else:
                    # Existing row - track ID and check for changes
                    url_id = int(row['ID'])
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
        if has_changes and st.session_state.table_save_message:
            st.session_state.table_save_message = None
        
        # Display save message below the table if it exists (from previous save)
        if st.session_state.table_save_message:
            st.success(st.session_state.table_save_message)
        
        if has_changes:
            if st.button("💾 Save Table"):
                # Process all changes
                changes_made = False
                errors = []
                
                # Create new rows
                for new_row in new_rows:
                    try:
                        result = create_test_url(
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
                        result = update_test_url(project['id'], url_id, **updates)
                        if result and result.get('success'):
                            changes_made = True
                    except Exception as e:
                        errors.append(f"Error updating URL {url_id}: {str(e)}")
                
                # Delete removed rows
                for url_id in deleted_ids:
                    try:
                        result = delete_test_url(project['id'], url_id)
                        if result and result.get('success'):
                            changes_made = True
                    except Exception as e:
                        errors.append(f"Error deleting URL {url_id}: {str(e)}")
                
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
                    st.session_state.table_save_message = f"✅ Saved! {' | '.join(summary)}"
                    # Toggle the flag to change the data_editor key, forcing a reset
                    # This ensures the widget starts fresh with saved data on next render
                    st.session_state.table_just_saved = not st.session_state.table_just_saved
                    st.rerun()
    else:
        st.info("ℹ️ No test URLs in database. Generate URLs from a query above.")
    
    st.markdown("---")
    
    # Section 2: Edit Lead Features
    st.markdown("## Step 2: Edit Lead Extraction Prompts")
    st.markdown("Configure the criteria for what makes a good lead. These features will be used in the extraction prompt.")
    
    # Get current values
    current_lead_features_we_want = project.get('lead_features_we_want', '')
    current_lead_features_to_avoid = project.get('lead_features_to_avoid', '')
    
    col1, col2 = st.columns(2)
    with col1:
        lead_features_we_want = st.text_area(
            "Lead Features We Want",
            value=current_lead_features_we_want,
            placeholder="e.g., Companies focused on sustainability, B2B SaaS companies, etc.",
            height=120,
            help="Describe the features or characteristics you want in your leads",
            key="test_lead_features_we_want"
        )
    with col2:
        lead_features_to_avoid = st.text_area(
            "Lead Features to Avoid",
            value=current_lead_features_to_avoid,
            placeholder="e.g., Polluters, greenwashing lists, fossil fuel companies, etc.",
            height=120,
            help="Describe the features or characteristics you want to avoid in your leads",
            key="test_lead_features_to_avoid"
        )
    
    # Save button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("💾 Save Prompts"):
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
                        st.success("✅ Lead features saved successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save lead features")
            else:
                st.info("ℹ️ No changes to save")
    
    st.markdown("---")
    
    # Section 3: Run Lead Extraction
    st.markdown("## Step 3: Run Lead Extraction")
    st.markdown("View the extracted leads from your test URLs:")
    
    if not test_urls:
        st.warning("⚠️ Please add at least one test URL above before running extraction.")
        st.button("🚀 Run Lead Extraction", disabled=True)
    else:
        if st.button("🚀 Run Lead Extraction"):
            # Clear previous results
            st.session_state.test_results = []
            
            with st.spinner(f"🔄 Running extraction on {len(test_urls)} URL(s)..."):
                try:
                    result = extract_test_leads(project['id'])
                    if result and result.get('success'):
                        # Store results in session state
                        extracted_leads = result.get('extracted_leads', [])
                        st.session_state.test_results = extracted_leads
                        st.success(f"✅ Extraction completed! Found leads in {len(extracted_leads)} URL(s)")
                        st.rerun()
                    else:
                        st.error("❌ Extraction failed")
                except Exception as e:
                    st.error(f"❌ Error during extraction: {str(e)}")
    
    # Section 4: Results Table
    if st.session_state.test_results:
        st.markdown("---")
        st.markdown("## 📊 Extraction Results")
        
        # Prepare data for summary table
        results_data = []
        for result in st.session_state.test_results:
            leads = result.get('leads', [])
            results_data.append({
                'URL': result['url'][:60] + '...' if len(result['url']) > 60 else result['url'],
                'Query': result.get('query', 'N/A'),
                'Leads Found': len(leads),
                'Leads': ', '.join(leads[:5]) + ('...' if len(leads) > 5 else '') if leads else 'None'
            })
        
        df = pd.DataFrame(results_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Show detailed results in expandable sections
        st.markdown("### 📋 Detailed Results")
        for i, result in enumerate(st.session_state.test_results):
            leads = result.get('leads', [])
            with st.expander(f"🔗 URL {i+1}: {result['url'][:80]}... ({len(leads)} leads)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Query:** {result.get('query', 'N/A')}")
                    st.markdown(f"**Title:** {result.get('title', 'N/A')}")
                with col2:
                    st.markdown(f"**Leads Found:** {len(leads)}")
                
                if result.get('snippet'):
                    st.markdown(f"**Snippet:** {result.get('snippet', '')}")
                
                if leads:
                    st.markdown("**Extracted Leads:**")
                    for lead in leads:
                        st.markdown(f"- {lead}")
                else:
                    st.info("No leads extracted from this URL")
    elif test_urls:
        st.info("ℹ️ Click 'Run Lead Extraction' above to see results for your test URLs.")
    
    st.markdown("---")
    
    # Back button at the end
    if st.button("← Back to Lead Collection", type="secondary", key="back_bottom"):
        st.session_state.current_page = "collect_leads"
        st.rerun()
