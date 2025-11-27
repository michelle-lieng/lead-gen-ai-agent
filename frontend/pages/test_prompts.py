"""
Test extraction prompts page
"""
import streamlit as st
import pandas as pd
from api_client import (
    update_project, get_project, 
    generate_test_urls, get_test_urls, update_test_url, delete_test_url, extract_test_leads
)

def init_test_prompts_session_state():
    """Initialize session state variables for test prompts page"""
    if 'test_results' not in st.session_state:
        st.session_state.test_results = []  # List of dicts: {url, query, title, snippet, extracted_companies, status}

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
    
    # Display test URLs as editable table
    if test_urls:
        st.markdown(f"Below you can add, edit and delete URLs:")
        
        # Convert to DataFrame for display
        urls_df = pd.DataFrame([
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
        
        # Display editable table (excluding ID and Status from editing)
        edited_df = st.data_editor(
            urls_df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "URL": st.column_config.TextColumn("URL", width="large", disabled=True),
                "Query": st.column_config.TextColumn("Query"),
                "Title": st.column_config.TextColumn("Title", width="medium"),
                "Snippet": st.column_config.TextColumn("Snippet", width="large"),
                "Status": st.column_config.TextColumn("Status", disabled=True)
            },
            disabled=["ID", "URL", "Status"],  # These columns are read-only
            key="test_urls_editor"
        )
        
        # Save changes button
        if not edited_df.equals(urls_df):
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 Save Changes", type="primary"):
                    # Find changed rows and update them
                    changes_made = False
                    for idx, row in edited_df.iterrows():
                        original_row = urls_df.iloc[idx]
                        url_id = int(row['ID'])
                        
                        # Check if any editable fields changed
                        updates = {}
                        if row['Query'] != original_row['Query']:
                            updates['query'] = row['Query']
                        if row['Title'] != original_row['Title']:
                            updates['title'] = row['Title']
                        if row['Snippet'] != original_row['Snippet']:
                            updates['snippet'] = row['Snippet']
                        
                        if updates:
                            try:
                                result = update_test_url(project['id'], url_id, **updates)
                                if result and result.get('success'):
                                    changes_made = True
                            except Exception as e:
                                st.error(f"❌ Error updating URL {url_id}: {str(e)}")
                    
                    if changes_made:
                        st.success("✅ Changes saved successfully!")
                        st.rerun()
            
            with col2:
                st.caption("💡 Make changes above and click 'Save Changes' to update the database")
        
        
        # Create checkboxes for deletion
        urls_to_delete = []
        for url in test_urls:
            if st.checkbox(
                f"Delete: {url['link'][:80]}...",
                key=f"delete_checkbox_{url['id']}"
            ):
                urls_to_delete.append(url['id'])
        
        if urls_to_delete:
            if st.button("🗑️ Delete Selected URLs", type="secondary"):
                deleted_count = 0
                for url_id in urls_to_delete:
                    try:
                        result = delete_test_url(project['id'], url_id)
                        if result and result.get('success'):
                            deleted_count += 1
                    except Exception as e:
                        st.error(f"❌ Error deleting URL {url_id}: {str(e)}")
                
                if deleted_count > 0:
                    st.success(f"✅ Deleted {deleted_count} URL(s)")
                    st.rerun()
    else:
        st.info("ℹ️ No test URLs in database. Generate URLs from a query above.")
    
    st.markdown("---")
    
    # Section 2: Edit Lead Features
    st.markdown("## Step 2: Edit Lead Extraction Prompts")
    st.markdown("Configure the criteria for what makes a good lead. These features will be used in the extraction prompt.")
    
    # Get current values
    current_lead_features_we_want = project.get('lead_features_we_want', '') or ''
    current_lead_features_to_avoid = project.get('lead_features_to_avoid', '') or ''
    
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
