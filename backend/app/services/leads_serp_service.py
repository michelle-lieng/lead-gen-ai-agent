
"""
Lead generation from search using AI-powered query generation
"""
import logging
import asyncio
import openai
import csv
from io import StringIO, BytesIO
from datetime import datetime
import re
import zipfile
from agents import Agent, Runner, set_default_openai_key
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, distinct
from sqlalchemy.exc import SQLAlchemyError

from .database_service import db_service
from .project_service import project_service
from .merged_results_service import merged_results_service
from ..exceptions import ProjectNotFoundError, DatabaseFailureError, InvalidProjectConfigurationError, ApiKeyNotConfiguredError, ExternalScraperError, UrlNotFoundError, DuplicateUrlError, OpenAITokenLimitExceededError

from ..utils.scrapers import jina_serp_scraper, jina_url_scraper
from ..utils.lead_utils import normalize_lead_name
from ..config import settings
from ..prompts import SERP_QUERIES_PROMPT, SERP_EXTRACTION_PROMPT
from ..models.tables import SerpQuery, SerpUrl, SerpLead, SerpLeadAggregated, Project
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
            raise ApiKeyNotConfiguredError("OpenAI API key not configured")
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)

        # for openai agents sdk
        set_default_openai_key(settings.openai_api_key)
        
        # Separate semaphores for each API type since they have different rate limits
        # and are used in different workflow stages
        self.serp_scraper_semaphore = asyncio.Semaphore(15)  # For jina_serp_scraper (increased from 10)
        self.url_scraper_semaphore = asyncio.Semaphore(15)    # For jina_url_scraper (increased from 10, Jina Reader API: 200 RPM)
        self.llm_semaphore = asyncio.Semaphore(3)             # For Runner.run (OpenAI API, reduced from 12 due to TPM limits: 30K TPM)

    def generate_search_queries_for_project(self, project_id: int, num_queries: int = 3) -> list[str]:
        """
        Generate AI-powered search queries for a project by project_id.
        Fetches the project query_search_target internally.
        
        Args:
            project_id (int): ID of the project
            num_queries (int): Number of queries to generate (default: 3)
        
        Returns:
            list[str]: List of generated search queries
        
        Raises:
            ProjectNotFoundError: If project with project_id does not exist
        """
        project = project_service.get_project(project_id)

        # Create the prompt for ChatGPT
        prompt = SERP_QUERIES_PROMPT.format(
            query_search_target=project.query_search_target, 
            num_queries=num_queries
        )
        
        # Call OpenAI API
        response = self.openai_client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": "You are an expert at generating effective Google search queries for lead generation. You create specific, descriptive queries that combine multiple terms, locations, and company characteristics to find the best potential leads. Your queries are natural, varied, creative, and optimized to discover company directories, lists, case studies, and business profiles."},
                {"role": "user", "content": prompt}
            ],
            text_format=QueryListRequest,
            temperature=0.7  # Higher temperature for more creative and varied queries
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

    def _add_queries_to_table(self, project_id: int, queries: list[str]) -> bool:
        """
        Save generated search queries to the database for a specific project.
        
        Args:
            project_id (int): ID of the project these queries belong to
            queries (list[str]): List of search queries to save
        
        Returns:
            bool: shows if successful or not
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
                
                logger.info(f"Uploaded {total_queries} queries to serp_queries table")
                return True
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error saving queries to database")
            raise DatabaseFailureError("Failed to save queries to database") from e

    async def _process_query(self, query: str, project_id: int) -> list[dict]:
        """Process a single query with semaphore protection for API calls"""
        async with self.serp_scraper_semaphore:
            serp_object = await jina_serp_scraper(query)  # Protected by serp_scraper_semaphore
            # ExternalScraperError will propagate to caller (caught in _generate_and_add_urls_to_table)
            query_urls = []
            for serp_result in serp_object:
                link = serp_result.get('url')
                if link:
                    query_urls.append({
                        'project_id': project_id,
                        'query': query,
                        'title': serp_result.get('title'),
                        'link': link,
                        'snippet': serp_result.get('description')
                    })
            return query_urls

    async def _generate_and_add_urls_to_table(self, project_id: int, queries: list[str]) -> dict:
        """
        1. first generate the urls using jina_serp_scraper
        2. then save urls to serp_urls table
        
        Returns:
            dict: Contains success status, URLs added, and statistics
        """
        try:
            with db_service.get_session() as session:
                # Process all queries in parallel using asyncio
                # ExternalScraperError from _process_query will propagate to caller
                tasks = [self._process_query(query, project_id) for query in queries]
                results = await asyncio.gather(*tasks)
                
                # STEP 1: Get existing URLs for this project to avoid duplicates
                existing_urls = session.query(SerpUrl.link).filter(
                    SerpUrl.project_id == project_id
                ).all()
                existing_links = {url.link for url in existing_urls}
                
                # STEP 2: Collect all generated urls first using jina_serp_scraper
                all_urls = []
                seen_links = set()  # Track unique links to avoid duplicates within this batch

                for query_urls in results:
                    for url_data in query_urls:
                        link = url_data['link']
                        # Only add if not already in project and not duplicate in this batch
                        if link not in seen_links and link not in existing_links:
                            seen_links.add(link)
                            all_urls.append(url_data)

                # Step 3: Batch upsert using SQLAlchemy core with composite unique constraint
                if all_urls:
                    statement = insert(SerpUrl).values(all_urls)
                    statement = statement.on_conflict_do_update(
                        index_elements=['project_id', 'link'],
                        set_=dict(
                            title=statement.excluded.title,
                            snippet=statement.excluded.snippet
                        )
                    )
                    session.execute(statement)
                    session.commit()
                    logger.info(f"✅ Processed {len(all_urls)} URLs for {len(queries)} queries")
                else:
                    logger.info(f"ℹ️ No new URLs to add (all were duplicates for project {project_id})")
            
            return {
                "success": True,
                "urls_added": len(all_urls),
                "queries_processed": len(queries),
                "message": f"Successfully added {len(all_urls)} URLs from {len(queries)} search queries"
            }
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error generating and saving URLs to database")
            raise DatabaseFailureError("Failed to generate and save URLs to database") from e

    async def save_queries_and_generate_urls(self, project_id: int, queries: list[str]) -> dict:
        """
        Orchestrates saving queries and generating URLs in one operation.
        This is the main business workflow that should be used by API routes.
        
        Args:
            project_id (int): ID of the project
            queries (list[str]): List of search queries to save and process
        
        Returns:
            dict: Unified response containing:
                - success: bool indicating overall success
                - queries_saved: bool indicating if queries were saved
                - urls_result: dict with URLs operation results
                - message: str with summary message
        
        Raises:
            ProjectNotFoundError: If project does not exist
            DatabaseFailureError: If database operation fails
        """
        # Step 1: Save queries to database
        queries_saved = self._add_queries_to_table(project_id, queries)
        
        # Step 2: Generate URLs from queries and save to database
        urls_result = await self._generate_and_add_urls_to_table(project_id, queries)
        
        # Combine results into unified response
        return {
            "success": queries_saved and urls_result.get("success", False),
            "queries_saved": queries_saved,
            "urls_result": urls_result,
            "message": f"Saved {len(queries)} queries and {urls_result.get('urls_added', 0)} URLs"
        }

    def get_urls(self, project_id: int) -> list[dict]:
        """
        Get all unprocessed production URLs for a project.
        
        Args:
            project_id (int): ID of the project
            
        Returns:
            list[dict]: List of URL dictionaries with id, project_id, query, title, link, 
                       snippet, website_scraped, status, created_at (only URLs with status="unprocessed")
                       
        Raises:
            DatabaseFailureError: If database operation fails
        """
        try:
            with db_service.get_session() as session:
                urls = session.query(SerpUrl).filter(
                    SerpUrl.project_id == project_id,
                    SerpUrl.status == "unprocessed"
                ).order_by(SerpUrl.created_at.desc()).all()
                
                return [
                    {
                        "id": url.id,
                        "project_id": url.project_id,
                        "query": url.query,
                        "title": url.title,
                        "link": url.link,
                        "snippet": url.snippet,
                        "website_scraped": url.website_scraped,
                        "status": url.status,
                        "created_at": url.created_at.isoformat() if url.created_at else None
                    }
                    for url in urls
                ]
        except SQLAlchemyError as e:
            logger.exception(f"Error fetching URLs for project {project_id}")
            raise DatabaseFailureError("Failed to fetch URLs") from e

    def create_url(self, project_id: int, link: str, title: str = None, snippet: str = None) -> dict:
        """
        Create a single production URL manually.
        
        Args:
            project_id (int): ID of the project
            link (str): URL link (required)
            title (str, optional): Title of the URL
            snippet (str, optional): Snippet/description of the URL
            
        Returns:
            dict: Contains success status, message, and created URL data
            
        Raises:
            DuplicateUrlError: If URL already exists in this project
            DatabaseFailureError: If database operation fails
        """
        try:
            with db_service.get_session() as session:
                # Check if URL already exists in this project (unique per project)
                existing = session.query(SerpUrl).filter(
                    SerpUrl.project_id == project_id,
                    SerpUrl.link == link
                ).first()
                
                if existing:
                    raise DuplicateUrlError(link, project_id)
                
                # Create new URL
                # Query is automatically set to "Manual Entry" for manually created URLs
                new_url = SerpUrl(
                    project_id=project_id,
                    link=link,
                    title=title or '',
                    snippet=snippet or '',
                    query='Manual Entry',  # Automatically set for manually created URLs
                    status="unprocessed"
                )
                
                session.add(new_url)
                session.commit()
                session.refresh(new_url)
                
                logger.info(f"Created URL {new_url.id} for project {project_id}")
                
                return {
                    "success": True,
                    "message": "URL created successfully",
                    "url": {
                        "id": new_url.id,
                        "project_id": new_url.project_id,
                        "query": new_url.query,
                        "title": new_url.title,
                        "link": new_url.link,
                        "snippet": new_url.snippet,
                        "status": new_url.status
                    }
                }
        except SQLAlchemyError as e:
            logger.exception(f"Error creating URL for project {project_id}")
            raise DatabaseFailureError("Failed to create URL") from e

    def update_url(self, project_id: int, url_id: int, title: str = None, snippet: str = None, link: str = None) -> dict:
        """
        Update a production URL (title, snippet or link).
        
        Args:
            project_id (int): ID of the project
            url_id (int): ID of the URL to update
            title (str, optional): New title
            snippet (str, optional): New snippet
            link (str, optional): New link
            
        Returns:
            dict: Contains success status, message, and updated URL data
            
        Raises:
            UrlNotFoundError: If URL not found
            DatabaseFailureError: If database operation fails
        """
        try:
            with db_service.get_session() as session:
                url = session.query(SerpUrl).filter(
                    SerpUrl.id == url_id,
                    SerpUrl.project_id == project_id
                ).first()
                
                if not url:
                    raise UrlNotFoundError(url_id, project_id)
                
                # Update fields if provided
                if title is not None:
                    url.title = title
                if snippet is not None:
                    url.snippet = snippet
                if link is not None:
                    # Check if the new link already exists in this project (excluding current URL)
                    existing = session.query(SerpUrl).filter(
                        SerpUrl.project_id == project_id,
                        SerpUrl.link == link,
                        SerpUrl.id != url_id
                    ).first()
                    
                    if existing:
                        raise DuplicateUrlError(link, project_id)
                    
                    url.link = link
                
                session.commit()
                
                logger.info(f"Updated URL {url_id} for project {project_id}")
                
                return {
                    "success": True,
                    "message": "URL updated successfully",
                    "url": {
                        "id": url.id,
                        "project_id": url.project_id,
                        "query": url.query,
                        "title": url.title,
                        "link": url.link,
                        "snippet": url.snippet,
                        "status": url.status
                    }
                }
        except SQLAlchemyError as e:
            logger.exception(f"Error updating URL {url_id} for project {project_id}")
            raise DatabaseFailureError("Failed to update URL") from e

    def delete_url(self, project_id: int, url_id: int) -> dict:
        """
        Delete a production URL.
        
        Args:
            project_id (int): ID of the project
            url_id (int): ID of the URL to delete
            
        Returns:
            dict: Contains success status and message
            
        Raises:
            UrlNotFoundError: If URL not found
            DatabaseFailureError: If database operation fails
        """
        try:
            with db_service.get_session() as session:
                url = session.query(SerpUrl).filter(
                    SerpUrl.id == url_id,
                    SerpUrl.project_id == project_id
                ).first()
                
                if not url:
                    raise UrlNotFoundError(url_id, project_id)
                
                session.delete(url)
                session.commit()
                
                logger.info(f"Deleted URL {url_id} for project {project_id}")
                
                return {
                    "success": True,
                    "message": "URL deleted successfully"
                }
        except SQLAlchemyError as e:
            logger.exception(f"Error deleting URL {url_id} for project {project_id}")
            raise DatabaseFailureError("Failed to delete URL") from e

    def _truncate_by_word_count(self, text: str, max_words: int) -> str:
        """
        Truncate text to max_words, cutting at word boundaries.
        
        OpenAI TPM limit: 30,000 tokens
        - ~1.3 tokens per word on average
        - Need to leave room for prompt, instructions, and output
        - Safe target: ~20,000 tokens for content = ~15,000 words
        """
        if not text:
            return text
        
        words = text.split()
        if len(words) <= max_words:
            return text
        
        # Truncate to max_words and rejoin
        truncated_words = words[:max_words]
        return ' '.join(truncated_words) + "\n\n[Content truncated due to token limit]"

    async def _process_url_and_extract_lead(self, url_data: dict, lead_minimum_criteria: str) -> dict:
        """Process a single URL and return result (using plain dict, not ORM object)"""
        url = url_data['link']
        query = url_data['query']
        title = url_data['title']
        snippet = url_data['snippet']
        
        try:
            logger.info(f"Processing URL: {url}")
            
            # Always scrape the URL first - protected by url_scraper_semaphore
            logger.info(f"Scraping URL: {url}")
            async with self.url_scraper_semaphore:
                scraped_content = await jina_url_scraper(url)

            # Format prompt with criteria
            extraction_prompt = SERP_EXTRACTION_PROMPT.format(lead_minimum_criteria=lead_minimum_criteria)
            
            # Create agent without tools (no tool calls needed)
            agent = Agent(
                name="Lead Generator",
                instructions=extraction_prompt,
                tools=[],  # No tools - we always scrape first
                output_type=list[str], # Specify the output type as a list of strings
            )
            
            # Track original scraped content for return value
            original_scraped_content = scraped_content
            # Start with full content, will truncate only if error occurs
            current_scraped_content = scraped_content if scraped_content else "No content available"
            
            # Run the agent with scraped content already in the input - protected by llm_semaphore
            # Retry logic: 3 retries max, parse wait time from error message
            max_retries = 3
            default_wait_time = 10.0  # Fallback if we can't parse the time
            
            leads = []
            for attempt in range(max_retries):
                # Build input text with current (possibly truncated) scraped content
                input_text = f"""
                    Search Result:
                    Query: {query}
                    Title: {title}
                    Snippet: {snippet}
                    URL: {url}

                    Scraped Content:
                    {current_scraped_content}
                    """
                try:
                    async with self.llm_semaphore:
                        result = await Runner.run(agent, input=input_text)
                    
                    logger.info(f"Final output (company names): {result.final_output}")
                    # enforce list type for leads
                    leads = result.final_output
                    scraped_content = original_scraped_content  # Use original, not truncated
                    break  # Success, exit retry loop

                except (TimeoutError, openai.APITimeoutError) as e:
                    # Timeout errors from OpenAI API (not scraper)
                    if attempt < max_retries - 1:
                        wait_time = min(2.0 * (2 ** attempt), 30.0)  # Exponential backoff: 2s, 4s, 8s (max 30s)
                        logger.warning(
                            f"⚠️ Timeout error for {url} (attempt {attempt + 1}/{max_retries}). "
                            f"Waiting {wait_time:.1f}s before retry..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise
                except openai.RateLimitError as e:
                    # Rate limit errors - retry with parsed wait time
                    if attempt < max_retries - 1:
                        error_str = str(e)
                        wait_time = default_wait_time
                        # Try to parse the retry time from the error message
                        retry_time_match = re.search(r'Please try again in ([\d.]+)s', error_str, re.IGNORECASE)
                        if retry_time_match:
                            try:
                                parsed_time = float(retry_time_match.group(1))
                                wait_time = max(parsed_time + 1.0, 2.0)  # Minimum 2 seconds
                            except ValueError:
                                # Invalid float format (e.g., "1.2.3"), use default
                                pass  # wait_time already set to default_wait_time
                        else:
                            # Try to match milliseconds
                            retry_time_match = re.search(r'Please try again in ([\d.]+)ms', error_str, re.IGNORECASE)
                            if retry_time_match:
                                try:
                                    parsed_time_ms = float(retry_time_match.group(1))
                                    parsed_time = parsed_time_ms / 1000.0
                                    wait_time = max(parsed_time + 1.0, 2.0)
                                except ValueError:
                                    # Invalid float format, use default
                                    pass  # wait_time already set to default_wait_time
                        
                        logger.warning(
                            f"⚠️ Rate limit error for {url} (attempt {attempt + 1}/{max_retries}). "
                            f"Waiting {wait_time:.1f}s before retry..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise
                except openai.BadRequestError as e:
                    # Check if it's a "request too large" error (truncate and retry)
                    error_str = str(e)
                    error_lower = error_str.lower()
                    is_request_too_large = (
                        "request too large" in error_lower or
                        "tokens must be reduced" in error_lower or
                        "maximum context length" in error_lower or
                        "token limit" in error_lower
                    )
                    
                    if is_request_too_large and attempt < max_retries - 1:
                        max_words = 10000
                        word_count = len(current_scraped_content.split())
                        if word_count > max_words:
                            current_scraped_content = self._truncate_by_word_count(current_scraped_content, max_words)
                            logger.warning(
                                f"⚠️ Request too large for {url} (attempt {attempt + 1}/{max_retries}). "
                                f"Truncating from {word_count} words to {max_words} words and retrying..."
                            )
                            await asyncio.sleep(1.0)
                            continue
                        else:
                            # Already at or below limit, can't truncate further
                            logger.error(
                                f"❌ Request too large for {url} even with {word_count} words. "
                                f"Error: {error_str}"
                            )
                            raise OpenAITokenLimitExceededError(f"Request too large: input exceeds token limit even after truncation. {error_str}")
                    else:
                        # Not a "request too large" error, or max retries reached
                        raise
            
            # Clean up leads - handle AI returning ['[]'] or similar
            if leads:
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
            
            # Determine status based on results
            if leads:
                status = "processed"
            else:
                status = "skip"
                logger.info(f"⏭️ No leads found in {url_data['link']} - marked as skip")
            
            return {
                'url_id': url_data['id'],
                'url': url_data['link'],
                'title': url_data['title'],
                'query': url_data['query'],
                'snippet': url_data['snippet'],
                'leads': leads,
                'scraped_content': scraped_content,
                'status': status,
                'error': None
            }
            
        except (ExternalScraperError, OpenAITokenLimitExceededError, TimeoutError, openai.APITimeoutError, openai.RateLimitError, openai.BadRequestError) as e:
            # External API errors only: scraper failures, retryable OpenAI errors, timeouts
            # OpenAITokenLimitExceededError is raised by our code for "request too large" that can't be truncated
            # Note: Non-retryable OpenAI errors are NOT caught - let them propagate to route layer:
            #   - openai.APIError: base class
            # Note: Programming errors (KeyError, TypeError, etc.) are NOT caught - they should propagate
            logger.exception(f"❌ Error processing {url_data['link']}")
            return {
                'url_id': url_data['id'],
                'url': url_data['link'],
                'title': url_data['title'],
                'query': url_data['query'],
                'snippet': url_data['snippet'],
                'leads': [],
                'scraped_content': None,
                'status': 'failed',
                'error': str(e)
            }

    async def extract_and_add_leads_to_table(self, project_id: int) -> dict:
        """
        Process unprocessed URLs from serp_urls table:
        1. Get all URLs with status="unprocessed" for the project
        2. Extract leads using _process_url_and_extract_lead (in parallel)
        3. Update website_scraped column with scraped content
        4. Update status based on results:
           - "processed" if leads found
           - "skip" if no leads found (empty list)
           - "failed" if extraction or saving failed
        5. Save extracted leads to serp_leads table
        
        Raises:
            ProjectNotFoundError: If project does not exist
            InvalidProjectConfigurationError: If lead_minimum_criteria is not set
            DatabaseFailureError: If database operation fails
        """
        try:
            with db_service.get_session() as session:
                # Step 0: Get project to retrieve lead_minimum_criteria
                project = project_service.get_project(project_id)  # Raises ProjectNotFoundError if not found
                lead_minimum_criteria = project.lead_minimum_criteria
                
                if not lead_minimum_criteria or not lead_minimum_criteria.strip():
                    raise InvalidProjectConfigurationError("Project does not have lead_minimum_criteria set. Please set it before extracting leads.")
                
                logger.info(f"Using lead minimum criteria for project {project_id}: {lead_minimum_criteria}")
                
                # Step 1: Get all unprocessed URLs for this project (only unprocessed, not failed)
                unprocessed_urls = session.query(SerpUrl).filter(
                    SerpUrl.project_id == project_id,
                    SerpUrl.status == "unprocessed"
                ).all()
                
                if not unprocessed_urls:
                    logger.info(f"No unprocessed URLs found for project {project_id}")
                    return {
                        "success": True,
                        "urls_processed": 0,
                        "urls_skipped": 0,
                        "urls_failed": 0,
                        "total_urls_attempted": 0,
                        "new_leads_extracted": 0,
                        "extracted_leads": [],
                        "message": "No unprocessed URLs found to extract leads from"
                    }
                
                logger.info(f"Processing {len(unprocessed_urls)} unprocessed URLs for project {project_id}")
                
                # Step 1.5: Extract data from ORM objects into plain dicts (detach before async)
                url_data_list = []
                for url_record in unprocessed_urls:
                    url_data_list.append({
                        'id': url_record.id,
                        'link': url_record.link,
                        'query': url_record.query,
                        'title': url_record.title,
                        'snippet': url_record.snippet
                    })
                
                # Step 2: Process URLs in parallel using asyncio
                # Process all URLs concurrently
                tasks = [self._process_url_and_extract_lead(url_data, lead_minimum_criteria) for url_data in url_data_list]
                results = await asyncio.gather(*tasks)
                
                # Step 3: Process results and update database (query fresh ORM objects by ID)
                processed_count = 0
                skipped_count = 0
                failed_count = 0
                new_leads_count = 0
                all_extracted_leads = []  # Collect all results to return in response
                
                for result in results:
                    url_id = result['url_id']
                    leads = result['leads']
                    scraped_content = result['scraped_content']
                    status = result['status']
                    
                    # Query fresh ORM object by ID (not using detached object)
                    url_record = session.query(SerpUrl).filter(SerpUrl.id == url_id).first()
                    if not url_record:
                        logger.error(f"❌ URL record {url_id} not found in database")
                        failed_count += 1
                        continue
                    
                    # Update the URL record
                    url_record.website_scraped = scraped_content
                    url_record.status = status
                    
                    if status == "failed":
                        failed_count += 1
                        all_extracted_leads.append({
                            "url": result['url'],
                            "title": result['title'],
                            "query": result['query'],
                            "snippet": result['snippet'],
                            "status": "failed",
                            "website_scraped": None,
                            "leads": []
                        })
                        continue
                    
                    if status == "processed":
                        processed_count += 1
                        
                        # Step 4: Save leads to serp_leads table (normalized)
                        try:
                            for lead in leads:
                                # Normalize lead name before saving (lowercase, trim whitespace)
                                normalized_lead = normalize_lead_name(lead)
                                
                                # Skip empty leads after normalization
                                if not normalized_lead:
                                    continue
                                
                                lead_record = SerpLead(
                                    project_id=project_id,
                                    serp_url_id=url_id,
                                    lead=normalized_lead  # Store normalized version
                                )
                                session.add(lead_record)
                                new_leads_count += 1
                            
                            logger.info(f"✅ Extracted {len(leads)} leads from {result['url']}")
                        except SQLAlchemyError as save_error:
                            # Failed to save leads - log but continue
                            logger.exception(f"❌ Failed to save leads for {result['url']}")
                            url_record.status = "failed"
                            failed_count += 1
                            processed_count -= 1  # Adjust count
                            all_extracted_leads.append({
                                "url": result['url'],
                                "title": result['title'],
                                "query": result['query'],
                                "snippet": result['snippet'],
                                "status": "failed",
                                "website_scraped": scraped_content,
                                "leads": []
                            })
                            continue
                    else:
                        skipped_count += 1
                    
                    # Store ALL results (processed, skipped) with status and scraped content
                    all_extracted_leads.append({
                        "url": result['url'],
                        "title": result['title'],
                        "query": result['query'],
                        "snippet": result['snippet'],
                        "status": status,
                        "website_scraped": scraped_content,
                        "leads": leads if leads else []
                    })
                
                # Commit all changes
                session.commit()
                
                logger.info(f"✅ Lead extraction completed for project {project_id}:")
                logger.info(f"   - Processed: {processed_count}")
                logger.info(f"   - Skipped: {skipped_count}")
                logger.info(f"   - Failed: {failed_count}")
                logger.info(f"   - New leads extracted: {new_leads_count}")
                
                # Transform leads to aggregated format after extraction
                aggregation_result = self._transform_leads_to_aggregated(project_id)
                logger.info(f"✅ Lead aggregation completed: {aggregation_result.get('message', '')}")
                
                # Merge aggregated leads into merged_results table
                merge_result = merged_results_service.merge_serp_leads(project_id)
                logger.info(f"✅ SERP leads merged: {merge_result.get('message', '')}")
                
                # Update project counts (including leads_collected from merged_results) after merge
                project_service.update_project_counts_from_db(project_id)
                                
                return {
                    "success": True,
                    "urls_processed": processed_count,
                    "urls_skipped": skipped_count,
                    "urls_failed": failed_count,
                    "total_urls_attempted": len(unprocessed_urls),
                    "new_leads_extracted": new_leads_count,
                    "extracted_leads": all_extracted_leads,  # Return detailed results for each URL
                    "message": f"Processed {processed_count} URLs, extracted {new_leads_count} new leads ({skipped_count} skipped, {failed_count} failed)"
                }
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error extracting leads from URLs")
            raise DatabaseFailureError("Failed to extract leads from URLs") from e
    
    def _transform_leads_to_aggregated(self, project_id: int) -> dict:
        """
        Transform SerpLead data into aggregated format grouped by lead name.
        Since leads are already normalized when saved, we can simply group by lead name
        and count distinct SERP URLs each lead appears in.
        
        Args:
            project_id: Project ID to aggregate leads for
            
        Returns:
            dict: Success status and statistics
        """
        try:
            with db_service.get_session() as session:
                # Validate project exists (raises ProjectNotFoundError if not found)
                project_service.get_project(project_id)
                
                # Query all SerpLead records for this project and group by lead name
                # Count distinct serp_url_ids for each lead (leads are already normalized)
                aggregated_data = session.query(
                    SerpLead.lead,
                    func.count(distinct(SerpLead.serp_url_id)).label('serp_count')
                ).filter(
                    SerpLead.project_id == project_id
                ).group_by(
                    SerpLead.lead
                ).all()
                
                if not aggregated_data:
                    logger.info(f"No leads found for project {project_id} to aggregate")
                    return {
                        "success": True,
                        "leads_aggregated": 0,
                        "message": "No leads found to aggregate"
                    }
                
                # Delete existing aggregated leads for this project to refresh the data
                session.query(SerpLeadAggregated).filter(
                    SerpLeadAggregated.project_id == project_id
                ).delete()
                
                # Insert fresh aggregated leads
                leads_aggregated_count = 0
                for lead_name, serp_count in aggregated_data:
                    aggregated_lead = SerpLeadAggregated(
                        project_id=project_id,
                        leads=lead_name,  # Already normalized (lowercase)
                        serp_count=serp_count
                    )
                    session.add(aggregated_lead)
                    leads_aggregated_count += 1
                
                session.commit()
                
                logger.info(f"✅ Aggregated {leads_aggregated_count} unique leads (new and old) for project {project_id}")
                
                return {
                    "success": True,
                    "leads_aggregated": leads_aggregated_count,
                    "message": f"Successfully aggregated {leads_aggregated_count} unique leads"
                }
                
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error transforming leads to aggregated format")
            raise DatabaseFailureError("Failed to transform leads to aggregated format") from e
    
    def _export_all_data_as_csv(self, project_id: int) -> dict:
        """
        Export ALL data as CSV(s) for all tables (queries, URLs, leads, leads_aggregated) for the project.
        No filtering - just returns everything.
        
        Args:
            project_id: Project ID
        
        Returns:
            dict: Contains CSV content as strings for queries, urls, leads, and leads_aggregated
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
                    writer.writerow(["query", "date_added"])
                    for record in queries:
                        writer.writerow([
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
                    writer.writerow(["id", "query", "title", "link", "snippet", "website_scraped", "status"])
                    for record in urls:
                        # Truncate website_scraped to 32600 characters to prevent CSV cell overflow (Excel limit is 32767)
                        website_scraped = record.website_scraped
                        if website_scraped and len(website_scraped) > 32600:
                            website_scraped = website_scraped[:32600]
                        writer.writerow([
                            record.id,
                            record.query,
                            record.title,
                            record.link,
                            record.snippet,
                            website_scraped or "",
                            record.status
                        ])
                    csv_files["urls"] = output.getvalue()
                
                # Get all leads for this project
                leads = session.query(SerpLead).filter(
                    SerpLead.project_id == project_id
                ).all()
                
                if leads:
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["serp_url_id", "lead"])
                    for record in leads:
                        writer.writerow([
                            record.serp_url_id,
                            record.lead
                        ])
                    csv_files["leads"] = output.getvalue()
                
                # Get all aggregated leads for this project, sorted by serp_count descending
                aggregated_leads = session.query(SerpLeadAggregated).filter(
                    SerpLeadAggregated.project_id == project_id
                ).order_by(
                    SerpLeadAggregated.serp_count.desc()
                ).all()
                
                if aggregated_leads:
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["leads", "serp_count"])
                    for record in aggregated_leads:
                        writer.writerow([
                            record.leads,
                            record.serp_count
                        ])
                    csv_files["leads_aggregated"] = output.getvalue()
            
            return {"csv_files": csv_files}
                
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error exporting data as CSV")
            raise DatabaseFailureError("Failed to export data as CSV") from e

    def export_all_data_as_zip(self, project_id: int) -> tuple[bytes | None, str | None]:
        """
        Export all project data as a ZIP file containing CSV files.
        
        This is the main export method that should be used by API routes.
        It generates a ZIP file with all project data (queries, URLs, leads, leads_aggregated) as CSV files.
        
        Args:
            project_id: Project ID
        
        Returns:
            tuple[bytes | None, str | None]: 
                - zip_file_bytes: Binary content of the ZIP file, or None if no data
                - filename: Suggested filename for download, or None if no data
        
        Raises:
            DatabaseFailureError: If database operation fails
        """
        try:
            # Step 1: Get CSV data using private method
            export_result = self._export_all_data_as_csv(project_id)
            csv_files = export_result.get("csv_files", {})
            
            # Step 2: Check if we have data (not an error, just no data)
            if not csv_files:
                return None, None
            
            # Step 3: Generate timestamp for filename
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Step 4: Get project name for meaningful filename
            project = project_service.get_project(project_id)
            project_name = project.project_name
            
            # Step 5: Sanitize project name for filename
            # Remove special characters, keep alphanumeric, spaces, hyphens, underscores
            safe_project_name = re.sub(r'[^\w\s-]', '', project_name).strip().replace(' ', '_')
            
            # Step 6: Generate ZIP filename
            zip_filename = f"{safe_project_name}_serp_lead_gen_{timestamp_str}.zip"
            
            # Step 7: Create ZIP file in memory
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for name, csv_content in csv_files.items():
                    # Encode CSV with UTF-8 BOM for Excel compatibility
                    zip_file.writestr(f"serp_{name}.csv", csv_content.encode('utf-8-sig'))
            
            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()
            
            logger.info(f"✅ Generated ZIP file for project {project_id}: {zip_filename} ({len(zip_bytes)} bytes)")
            
            return zip_bytes, zip_filename
                
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error exporting data as ZIP")
            raise DatabaseFailureError("Failed to export data as ZIP") from e

# Global project service instance
leads_serp_service = LeadsSerpService()