"""
Review leads page
"""
import streamlit as st
import pandas as pd
from api_client import get_merged_results, fetch_merged_results_zip

def show_review_leads():
    """Review leads page"""
    project = st.session_state.selected_project
    project_id = project['id']
    
    st.markdown(f"# 📋 Review Leads - {project['project_name']}")
    st.markdown("---")
    
    # Header with refresh and download buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📊 Merged Leads Table")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Fetch merged results
    try:
        result = get_merged_results(project_id)
        
        if result and result.get('data'):
            leads_data = result['data']
            columns = result['columns']
            count = result.get('count', len(leads_data))
            
            # Convert to DataFrame for display
            df = pd.DataFrame(leads_data)
            
            # Display stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Leads", count)
            with col2:
                serp_count = df['serp_count'].sum() if 'serp_count' in df.columns else 0
                st.metric("Total SERP Count", int(serp_count) if pd.notna(serp_count) else 0)
            with col3:
                enrichment_cols = [c for c in columns if c not in ['id', 'project_id', 'lead', 'serp_count']]
                st.metric("Enrichment Columns", len(enrichment_cols))
            
            st.markdown("---")
            
            # Display table
            st.markdown("### 📋 Leads Table")
            # Hide internal columns for cleaner display (optional)
            display_columns = [c for c in columns if c not in ['id', 'project_id']]
            display_df = df[display_columns] if all(c in df.columns for c in display_columns) else df
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Download button
            st.markdown("---")
            st.markdown("### 📤 Download")
            
            # Download button - fetch on click
            download_key = f"download_{project_id}"
            if download_key not in st.session_state:
                st.session_state[download_key] = None
            
            if st.button("📥 Download Merged Results as CSV", use_container_width=True, type="primary"):
                try:
                    with st.spinner("Preparing download..."):
                        zip_content, filename = fetch_merged_results_zip(project_id)
                        
                        if zip_content and filename:
                            st.session_state[download_key] = (zip_content, filename)
                            st.rerun()
                        else:
                            st.error("❌ Failed to fetch download. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error downloading: {str(e)}")
            
            # Show download button if we have the data
            if st.session_state[download_key]:
                zip_content, filename = st.session_state[download_key]
                st.download_button(
                    label="⬇️ Click to Download",
                    data=zip_content,
                    file_name=filename,
                    mime="application/zip",
                    use_container_width=True,
                    key=f"download_btn_{project_id}"
                )
                st.success(f"✅ Download ready: {filename}")
        else:
            st.info("ℹ️ No merged leads available yet. Start collecting leads or upload datasets to see them here!")
            
    except Exception as e:
        st.error(f"❌ Error loading leads: {str(e)}")
        st.info("ℹ️ Make sure you have run lead extraction or uploaded datasets for this project.")
