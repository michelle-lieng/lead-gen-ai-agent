
"""
Lead generation from search using AI-powered query generation
"""
import os
import logging
import asyncio
from openai import OpenAI
import csv
from io import StringIO
from agents import Agent, Runner, function_tool,set_default_openai_key
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert

from .database_service import db_service
from .project_service import project_service

from ..utils.scrapers import jina_serp_scraper, jina_url_scraper
from ..config import settings
from ..prompts import SERP_QUERIES_PROMPT, SERP_EXTRACTION_PROMPT
from ..models.tables import SerpQuery, SerpUrl, SerpLead
from ..models.schemas import QueryListRequest

logger = logging.getLogger(__name__)

# Disable noisy third-party logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

class LeadsSerpService:
    """Service for generating leads from search operations"""
    
    def __init__(self):
        """Initialise leads from search service with database service"""
        # Initialize OpenAI client once
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

        # for openai agents sdk
        set_default_openai_key(settings.openai_api_key)

    def generate_search_queries(self, description: str, num_queries: int = 3) -> list[str]:
        """
        Generate AI-powered search queries based on project description using ChatGPT
        
        Args:
            description (str): Project description to base queries on
            num_queries (int): Number of queries to generate (default: 3)
        
        Returns:
            list[str]: List of generated search queries
        """
        try:
            
            # Create the prompt for ChatGPT
            prompt = SERP_QUERIES_PROMPT.format(
                description=description, 
                num_queries=num_queries
            )
            
            # Call OpenAI API
            response = self.openai_client.responses.parse(
                model="gpt-4o-2024-08-06",
                input=[
                    {"role": "system", "content": "You are an expert at generating targeted search queries for lead generation. Generate precise, effective search queries that will find relevant companies."},
                    {"role": "user", "content": prompt}
                ],
                text_format=QueryListRequest,
                temperature=0.2
            )
            
            # Parse the response
            queries_object = response.output_parsed
            
            # Clean up any quotes or formatting issues
            cleaned_queries = []
            for query in queries_object.queries:
                # Remove quotes and extra whitespace
                cleaned_query = query.strip().strip('"').strip("'")
                cleaned_queries.append(cleaned_query)
            
            return cleaned_queries
            
        except Exception as e:
            logging.error(f"Error generating search queries: {str(e)}")
            raise

    def add_queries_to_table(self, project_id: int, queries: list[str]) -> bool:
        """
        Save generated search queries to the database for a specific project.
        
        Args:
            project_id (int): ID of the project these queries belong to
            queries (list[str]): List of search queries to save
        
        Returns:
            bool: shows if successiveful or not
        """
        try:
            total_queries = 0
            with db_service.get_session() as session:
                for query in queries:
                    # Create a new SerpQuery record
                    query_record = SerpQuery(
                        project_id=project_id,
                        query=query
                    )
                    session.add(query_record)
                    total_queries += 1
                
                # Commit all queries at once
                session.commit()
                
                logging.info(f"Uploaded {total_queries} queries to serp_queries table")
                return True
                
        except Exception as e:
            logging.error(f"❌ Error saving queries to database: {str(e)}")
            # Check if it's a foreign key violation
            if "ForeignKeyViolation" in str(e):
                raise ValueError(f"Project with ID {project_id} does not exist. Please create the project first.")
            raise

    def generate_and_add_urls_to_table(self, project_id: int, queries: list[str]) -> dict:
        """
        1. first generate the urls using jina_serp_scraper
        2. then save urls to serp_urls table
        
        Returns:
            dict: Contains success status, URLs added, and statistics
        """
        try:
            with db_service.get_session() as session:
                all_urls = []

                # STEP 1: Collect all generated urls first using jina_serp_scraper
                for query in queries:
                    # extract the urls using Serpapi
                    serp_object = jina_serp_scraper(query)
                    for serp_result in serp_object:
                        all_urls.append({
                            'project_id': project_id,
                            'query': query,
                            'title': serp_result.get('title'),
                            'link': serp_result.get('url'),
                            'snippet': serp_result.get('description')
                        })

                # Step 2: Batch upsert using SQLAlchemy core
                statement = insert(SerpUrl).values(all_urls)
                statement = statement.on_conflict_do_update(
                    index_elements=['link'],
                    set_=dict(
                        title=statement.excluded.title,
                        snippet=statement.excluded.snippet
                    )
                )
                session.execute(statement)
                session.commit()
                logging.info(f"✅ Processed {len(all_urls)} URLs for {len(queries)} queries")
            
            return {
                "success": True,
                "urls_added": len(all_urls),
                "queries_processed": len(queries),
                "message": f"Successfully added {len(all_urls)} URLs from {len(queries)} search queries"
            }
                
        except Exception as e:
            logging.error(f"❌ Error saving queries to database: {str(e)}")
            # Check if it's a foreign key violation
            if "ForeignKeyViolation" in str(e):
                raise ValueError(f"Project with ID {project_id} does not exist. Please create the project first.")
            raise

    # we use this decorator for tools to openai agent sdk
    @function_tool
    async def _scrape_url(url: str) -> str:
        """
        This tool asynchronously scrapes the url provided and returns a string of the website scraped.
        Use this tool when the search result seems to provide relevant leads e.g. 
        "Top 100 environmental companies" and you need more information than what is provided in the
        snippet and title to extract leads.
        """
        logging.info(f"Scraping URL: {url}")
        return jina_url_scraper(url)
    
    async def _lead_extractor(self, query, title, snippet, url) -> tuple[list, str | None]:
        """
        If on table serp_urls the status is unprocessed then we will scrape it.
        """
        agent = Agent(
            name="Lead Generator",
            instructions=SERP_EXTRACTION_PROMPT,
            tools=[self._scrape_url],
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
                logging.info("Tool output (scraped content) found.")
        logging.info(f"Final output (company names): {result.final_output}")
        # enforce list type for leads
        leads = result.final_output
        return leads, scraped_content
    
    async def extract_and_add_leads_to_table(self, project_id: int) -> bool:
        """
        Process unprocessed and failed URLs from serp_urls table:
        1. Get all URLs with status="unprocessed" or "failed" for the project (failed URLs can be retried)
        2. Extract leads using _lead_extractor
        3. Update website_scraped column with scraped content
        4. Update status based on results:
           - "processed" if leads found
           - "skip" if no leads found (empty list)
           - "failed" if extraction or saving failed (will be retried on next run)
        5. Save extracted leads to serp_leads table
        """
        try:
            with db_service.get_session() as session:
                # Step 1: Get all unprocessed and failed URLs for this project (failed can be retried)
                unprocessed_urls = session.query(SerpUrl).filter(
                    SerpUrl.project_id == project_id,
                    SerpUrl.status.in_(["unprocessed", "failed"])
                ).all()
                
                if not unprocessed_urls:
                    logging.info(f"No unprocessed or failed URLs found for project {project_id}")
                    return {
                        "success": True,
                        "urls_processed": 0,
                        "urls_skipped": 0,
                        "urls_failed": 0,
                        "total_urls_attempted": 0,
                        "new_leads_extracted": 0,
                        "message": "No unprocessed or failed URLs found to extract leads from"
                    }
                
                logging.info(f"Processing {len(unprocessed_urls)} URLs (unprocessed and failed) for project {project_id}")
                
                processed_count = 0
                skipped_count = 0
                failed_count = 0
                new_leads_count = 0
                
                # Step 2: Process each URL
                for url_record in unprocessed_urls:
                    try:
                        logging.info(f"Processing URL: {url_record.link}")
                        
                        # Extract leads using the _lead_extractor method
                        try:
                            leads, scraped_content = await self._lead_extractor(
                                query=url_record.query,
                                title=url_record.title,
                                snippet=url_record.snippet,
                                url=url_record.link
                            )
                        except Exception as extract_error:
                            # Extraction failed - log but continue processing
                            logging.error(f"❌ Extraction error for {url_record.link}: {str(extract_error)}")
                            url_record.status = "failed"
                            url_record.website_scraped = None
                            failed_count += 1
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
                            logging.info(f"Cleaned leads: {leads}")
                        
                        # Step 3: Update the URL record
                        url_record.website_scraped = scraped_content
                        
                        # Step 4: Determine status based on results
                        if leads and isinstance(leads, list) and len(leads) > 0:
                            # Leads found - mark as processed
                            url_record.status = "processed"
                            processed_count += 1
                            
                            # Step 5: Save leads to serp_leads table
                            try:
                                for lead in leads:
                                    lead_record = SerpLead(
                                        project_id=project_id,
                                        serp_url_id=url_record.id,
                                        lead=lead
                                    )
                                    session.add(lead_record)
                                    new_leads_count += 1
                                
                                logging.info(f"✅ Extracted {len(leads)} leads from {url_record.link}")
                            except Exception as save_error:
                                # Failed to save leads - log but continue
                                logging.error(f"❌ Failed to save leads for {url_record.link}: {str(save_error)}")
                                url_record.status = "failed"
                                failed_count += 1
                                continue
                            
                        else:
                            # No leads found - mark as skip
                            url_record.status = "skip"
                            skipped_count += 1
                            logging.info(f"⏭️ No leads found in {url_record.link} - marked as skip")
                            
                    except Exception as e:
                        # Unexpected error - mark as failed and continue processing
                        logging.error(f"❌ Unexpected error processing {url_record.link}: {str(e)}")
                        url_record.status = "failed"
                        url_record.website_scraped = None
                        failed_count += 1
                        # Continue to next URL - don't let one failure stop the whole process
                
                # Commit all changes
                session.commit()
                
                logging.info(f"✅ Lead extraction completed for project {project_id}:")
                logging.info(f"   - Processed: {processed_count}")
                logging.info(f"   - Skipped: {skipped_count}")
                logging.info(f"   - Failed: {failed_count}")
                logging.info(f"   - New leads extracted: {new_leads_count}")
                
                # Update project counts (urls_processed and leads_collected)
                project_service.update_project_counts_from_db(project_id)
                
                return {
                    "success": True,
                    "urls_processed": processed_count,
                    "urls_skipped": skipped_count,
                    "urls_failed": failed_count,
                    "total_urls_attempted": len(unprocessed_urls),
                    "new_leads_extracted": new_leads_count,
                    "message": f"Processed {processed_count} URLs, extracted {new_leads_count} new leads ({skipped_count} skipped, {failed_count} failed)"
                }
                
        except Exception as e:
            logging.error(f"❌ Error saving queries to database: {str(e)}")
            # Check if it's a foreign key violation
            if "ForeignKeyViolation" in str(e):
                raise ValueError(f"Project with ID {project_id} does not exist. Please create the project first.")
            raise
    
    def export_all_data_as_csv(self, project_id: int) -> dict:
        """
        Export ALL data as CSV(s) for all tables (queries, URLs, leads) for the project.
        No filtering - just returns everything.
        
        Args:
            project_id: Project ID
        
        Returns:
            dict: Contains CSV content as strings for queries, urls, and leads
        """
        try:
            with db_service.get_session() as session:
                csv_files = {}
                
                # Get all queries for this project
                queries = session.query(SerpQuery).filter(
                    SerpQuery.project_id == project_id
                ).all()
                
                if queries:
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["id", "project_id", "query", "date_added"])
                    for record in queries:
                        writer.writerow([
                            record.id,
                            record.project_id,
                            record.query,
                            record.date_added.isoformat()
                        ])
                    csv_files["queries"] = output.getvalue()
                
                # Get all URLs for this project
                urls = session.query(SerpUrl).filter(
                    SerpUrl.project_id == project_id
                ).all()
                
                if urls:
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["id", "project_id", "query", "title", "link", "snippet", "website_scraped", "status", "created_at"])
                    for record in urls:
                        # Truncate website_scraped to 32600 characters to prevent CSV cell overflow (Excel limit is 32767)
                        website_scraped = record.website_scraped
                        if website_scraped and len(website_scraped) > 32600:
                            website_scraped = website_scraped[:32600]
                        writer.writerow([
                            record.id,
                            record.project_id,
                            record.query,
                            record.title,
                            record.link,
                            record.snippet,
                            website_scraped or "",
                            record.status,
                            record.created_at.isoformat()
                        ])
                    csv_files["urls"] = output.getvalue()
                
                # Get all leads for this project
                leads = session.query(SerpLead).filter(
                    SerpLead.project_id == project_id
                ).all()
                
                if leads:
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["id", "project_id", "serp_url_id", "lead", "created_at"])
                    for record in leads:
                        writer.writerow([
                            record.id,
                            record.project_id,
                            record.serp_url_id,
                            record.lead,
                            record.created_at.isoformat()
                        ])
                    csv_files["leads"] = output.getvalue()
            
            return {"csv_files": csv_files}
                
        except Exception as e:
            logging.error(f"❌ Error exporting data as CSV: {str(e)}")
            raise

# Global project service instance
leads_serp_service = LeadsSerpService()

if __name__ == "__main__":
    #print(leads_serp_service.generate_search_queries("Best sushi stores in Australia")[0])
    #print(leads_serp_service.jina_serp_scrape("Best sushi stores in Australia")
    #print(leads_serp_service.add_queries_to_table(3, ["What is a dog","Pizza?"]))
    #print(leads_serp_service.generate_and_add_urls_to_table(2, ["Coles company greenwashing","Pizza?"]))
    
    # CASE 1: Easy company extraction
    # query = "what are the top environmental corporates in australia"
    # title = "Orica crowned Australia’s most sustainable company for Impact"
    # snippet = "Orica's success this year follows Acconia, an infrastucture and renewable..."
    # url = "https://www.afr.com/companies/mining/orica-crowned-australia-s-most-sustainable-company-for-impact-20240625-p5jojc"

    # CASE 2: Need to scrape
    # query = "what are the top environmental corporates in australia"
    # title = "crowned Australia’s most sustainable company for Impact"
    # snippet = "an infrastucture and renewable..."
    # url = "https://www.afr.com/companies/mining/orica-crowned-australia-s-most-sustainable-company-for-impact-20240625-p5jojc"

    # CASE 3: Should return empty list
    # query = "what are the top environmental corporates in australia"
    # title = "Top 14 Most Polluting Companies in 2023"
    # url = "https://www.theecoexperts.co.uk"
    # snippet = "5 June 2025 — The Top 10 Most Polluting Companies · 1. Saudi Aramco · 2. Chevron · 3. Gazprom · 4. ExxonMobil · 5. National Iranian Oil Company (NIOC) · 6. BP · 7."
    # leads, scraped_content = asyncio.run(leads_serp_service._lead_extractor(query, title, snippet, url))
    # print(leads)
    
    print(asyncio.run(leads_serp_service.extract_and_add_leads_to_table(3)))

