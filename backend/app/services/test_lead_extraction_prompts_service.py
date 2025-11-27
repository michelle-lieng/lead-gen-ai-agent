
"""
Service for testing lead extraction prompts using test URLs
"""
import logging
from agents import Agent, Runner, function_tool, set_default_openai_key
from sqlalchemy.dialects.postgresql import insert

from .database_service import db_service
from ..utils.scrapers import jina_serp_scraper, jina_url_scraper
from ..config import settings
from ..prompts import SERP_EXTRACTION_PROMPT
from ..models.tables import TestSerpUrl

logger = logging.getLogger(__name__)

# Disable noisy third-party logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

class TestLeadExtractionPromptsService:
    """Service for testing lead extraction prompts using test URLs"""
    
    def __init__(self):
        """Initialize test lead prompts service"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        # Set default OpenAI key for agents SDK
        set_default_openai_key(settings.openai_api_key)

    def generate_and_add_test_urls_to_table(self, project_id: int, query: str) -> dict:
        """
        1. first generate the urls using jina_serp_scraper
        2. then save urls to test_serp_urls table
        
        Returns:
            dict: Contains success status, URLs added, and statistics
        """
        try:
            with db_service.get_session() as session:
                # STEP 1: Collect all generated urls first using jina_serp_scraper
                all_urls = []
                seen_links = set()  # Track unique links to avoid duplicates
                
                # extract the urls using Serpapi
                serp_object = jina_serp_scraper(query)
                for serp_result in serp_object:
                    link = serp_result.get('url')
                    # Only add if we haven't seen this link before in this batch
                    if link and link not in seen_links:
                        seen_links.add(link)
                        all_urls.append({
                            'project_id': project_id,
                            'query': query,
                            'title': serp_result.get('title'),
                            'link': link,
                            'snippet': serp_result.get('description')
                        })

                # Step 2: Batch upsert using SQLAlchemy core - save to TestSerpUrl table
                statement = insert(TestSerpUrl).values(all_urls)
                statement = statement.on_conflict_do_update(
                    index_elements=['link'],
                    set_=dict(
                        title=statement.excluded.title,
                        snippet=statement.excluded.snippet
                    )
                )
                session.execute(statement)
                session.commit()
                logger.info(f"✅ Processed {len(all_urls)} test URLs for query: {query}")
            
            return {
                "success": True,
                "urls_added": len(all_urls),
                "message": f"Successfully added {len(all_urls)} test URLs from search query"
            }
                
        except Exception as e:
            logger.error(f"❌ Error saving queries to database: {str(e)}")
            # Check if it's a foreign key violation
            if "ForeignKeyViolation" in str(e):
                raise ValueError(f"Project with ID {project_id} does not exist. Please create the project first.")
            raise

    # we use this decorator for tools to openai agent sdk
    @function_tool
    async def _scrape_test_url(url: str) -> str:
        """
        This tool asynchronously scrapes the url provided and returns a string of the website scraped.
        Use this tool when the search result seems to provide relevant leads e.g. 
        "Top 100 environmental companies" and you need more information than what is provided in the
        snippet and title to extract leads.
        """
        logger.info(f"Scraping URL: {url}")
        return jina_url_scraper(url)
    
    async def _test_lead_extractor(self, query, title, snippet, url) -> tuple[list, str | None]:
        """
        Extract leads from test URLs for prompt testing/validation.
        Returns extracted leads and scraped content (if any).
        """
        agent = Agent(
            name="Lead Generator",
            instructions=SERP_EXTRACTION_PROMPT,
            tools=[self._scrape_test_url],
            output_type=list[str], # Specify the output type as a list of strings

        )
        # this runner class is async -> Runner.run(), which runs async and returns a RunResult. 
        result = await Runner.run(agent, 
                                input=f"""
                                    Search Result:
                                    Query: {query}
                                    Title: {title}
                                    Snippet: {snippet}
                                    URL: {url}
                                """)
        scraped_content = None #initial value
        for item in result.new_items:
            if getattr(item, "type", None) == "tool_call_output_item":
                scraped_content = getattr(item, "output", None)

                # scraped content is already cleaned by jina_url_scraper
                logger.info("Tool output (scraped content) found.")
        logger.info(f"Final output (company names): {result.final_output}")
        # enforce list type for leads
        leads = result.final_output
        return leads, scraped_content
    
    async def extract_test_leads(self, project_id: int) -> dict:
        """
        Process all URLs from test_serp_urls table:
        1. Reset all test URLs for the project to status="unprocessed" (allows re-running extraction)
        2. Get all test URLs for the project
        3. Extract leads using _test_lead_extractor
        4. Update website_scraped column with scraped content
        5. Update status based on results:
           - "processed" if leads found
           - "skip" if no leads found (empty list)
           - "failed" if extraction failed
        6. Return extracted leads in response (DO NOT save to database - these are just for prompt testing)
        
        Note: Test leads are NOT saved to serp_leads table. They're only returned for review
        to help iterate on the extraction prompt.
        """
        try:
            with db_service.get_session() as session:
                # Step 1: Reset all test URLs for this project to "unprocessed" status
                # This allows re-running extraction on all URLs when testing prompts
                session.query(TestSerpUrl).filter(
                    TestSerpUrl.project_id == project_id
                ).update({"status": "unprocessed"})
                session.commit()
                
                # Step 2: Get all test URLs for this project (now all are unprocessed)
                unprocessed_urls = session.query(TestSerpUrl).filter(
                    TestSerpUrl.project_id == project_id
                ).all()
                
                if not unprocessed_urls:
                    logger.info(f"No test URLs found for project {project_id}")
                    return {
                        "success": True,
                        "urls_processed": 0,
                        "urls_skipped": 0,
                        "urls_failed": 0,
                        "total_urls_attempted": 0,
                        "extracted_leads": [],
                        "message": "No test URLs found to extract leads from"
                    }
                
                logger.info(f"Processing {len(unprocessed_urls)} test URLs for project {project_id} (all statuses reset to unprocessed)")
                
                processed_count = 0
                skipped_count = 0
                failed_count = 0
                all_extracted_leads = []  # Collect all results to return in response (including skipped/failed)
                
                # Step 2: Process each URL
                for url_record in unprocessed_urls:
                    try:
                        logger.info(f"Processing test URL: {url_record.link}")
                        
                        # Extract leads using the _test_lead_extractor method
                        leads = []
                        scraped_content = None
                        try:
                            leads, scraped_content = await self._test_lead_extractor(
                                query=url_record.query,
                                title=url_record.title,
                                snippet=url_record.snippet,
                                url=url_record.link
                            )
                        except Exception as extract_error:
                            # Extraction failed - log but continue processing
                            logger.error(f"❌ Extraction error for {url_record.link}: {str(extract_error)}")
                            url_record.status = "failed"
                            url_record.website_scraped = None
                            failed_count += 1
                            
                            # Add failed URL to results
                            all_extracted_leads.append({
                                "url": url_record.link,
                                "title": url_record.title,
                                "query": url_record.query,
                                "snippet": url_record.snippet,
                                "status": "failed",
                                "website_scraped": None,
                                "leads": []
                            })
                            continue  # Skip to next URL
                        
                        # Clean up leads - handle AI returning ['[]'] or similar
                        if leads and isinstance(leads, list):
                            # Remove any strings that look like empty lists or invalid entries
                            cleaned_leads = []
                            for lead in leads:
                                if isinstance(lead, str):
                                    # Remove quotes and brackets, check if it's meaningful
                                    clean_lead = lead.strip().strip('[]').strip("'").strip('"')
                                    if clean_lead and clean_lead not in ['', '[]', 'None', 'null']:
                                        cleaned_leads.append(clean_lead)
                                elif lead and str(lead).strip():
                                    cleaned_leads.append(str(lead).strip())
                            
                            leads = cleaned_leads
                            logger.info(f"Cleaned leads: {leads}")
                        
                        # Step 3: Update the URL record
                        url_record.website_scraped = scraped_content
                        
                        # Step 4: Determine status based on results
                        if leads and isinstance(leads, list) and len(leads) > 0:
                            # Leads found - mark as processed
                            url_record.status = "processed"
                            processed_count += 1
                            
                            logger.info(f"✅ Extracted {len(leads)} leads from {url_record.link}")
                            
                        else:
                            # No leads found - mark as skip
                            url_record.status = "skip"
                            skipped_count += 1
                            logger.info(f"⏭️ No leads found in {url_record.link} - marked as skip")
                        
                        # Store ALL results (processed, skipped) with status and scraped content
                        all_extracted_leads.append({
                            "url": url_record.link,
                            "title": url_record.title,
                            "query": url_record.query,
                            "snippet": url_record.snippet,
                            "status": url_record.status,
                            "website_scraped": url_record.website_scraped,
                            "leads": leads if leads else []
                        })
                            
                    except Exception as e:
                        # Unexpected error - mark as failed and continue processing
                        logger.error(f"❌ Unexpected error processing {url_record.link}: {str(e)}")
                        url_record.status = "failed"
                        url_record.website_scraped = None
                        failed_count += 1
                        
                        # Add failed URL to results
                        all_extracted_leads.append({
                            "url": url_record.link,
                            "title": url_record.title,
                            "query": url_record.query,
                            "snippet": url_record.snippet,
                            "status": "failed",
                            "website_scraped": None,
                            "leads": []
                        })
                        # Continue to next URL - don't let one failure stop the whole process
                
                # Commit all changes (status and website_scraped updates)
                session.commit()
                
                logger.info(f"✅ Test lead extraction completed for project {project_id}:")
                logger.info(f"   - Processed: {processed_count}")
                logger.info(f"   - Skipped: {skipped_count}")
                logger.info(f"   - Failed: {failed_count}")
                logger.info(f"   - Total leads extracted: {sum(len(item['leads']) for item in all_extracted_leads)}")
                                
                return {
                    "success": True,
                    "urls_processed": processed_count,
                    "urls_skipped": skipped_count,
                    "urls_failed": failed_count,
                    "total_urls_attempted": len(unprocessed_urls),
                    "extracted_leads": all_extracted_leads,  # Return leads for review (not saved to DB)
                    "message": f"Processed {processed_count} test URLs, extracted leads from {len(all_extracted_leads)} URLs ({skipped_count} skipped, {failed_count} failed). Leads are returned for review only - not saved to database."
                }
                
        except Exception as e:
            logger.error(f"❌ Error extracting test leads: {str(e)}")
            # Check if it's a foreign key violation
            if "ForeignKeyViolation" in str(e):
                raise ValueError(f"Project with ID {project_id} does not exist. Please create the project first.")
            raise

# Global service instance
test_lead_extraction_prompts_service = TestLeadExtractionPromptsService()

