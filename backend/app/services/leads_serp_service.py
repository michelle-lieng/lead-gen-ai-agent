
"""
Lead generation from search using AI-powered query generation
"""
from openai import OpenAI
from pydantic import BaseModel
import os
from serpapi import GoogleSearch
import logging
from sqlalchemy.dialects.postgresql import insert

from .database_service import db_service

from ..config import settings
from ..models.tables import SerpQueries, SerpUrls
from ..models.schemas import QueryListRequest

logger = logging.getLogger(__name__)

class LeadsSerpService:
    """Service for generating leads from search operations"""
    
    def __init__(self):
        """Initialise leads from search service with database service"""
        # Initialize OpenAI client once
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def generate_search_queries(self, description: str, num_queries: int = 2) -> list[str]:
        """
        Generate AI-powered search queries based on project description using ChatGPT
        
        Args:
            description (str): Project description to base queries on
            num_queries (int): Number of queries to generate (default: 5)
        
        Returns:
            list[str]: List of generated search queries
        """
        try:
            
            # Create the prompt for ChatGPT
            prompt = f"""
            Based on this project description, generate {num_queries} targeted search queries to find potential leads:
            
            Project Description: {description}
            
            Requirements:
            - Generate search queries that would find companies matching this description
            - Include industry-specific terms, location keywords, and company size indicators
            - Make queries specific enough to find relevant results but broad enough to capture variety
            - Focus on terms that would appear in company websites, LinkedIn profiles, and business directories
            - Each query should be 3-8 words long
            """
            
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
            
            return queries_object.queries #returns a list
            
        except Exception as e:
            logging.error(f"Error generating search queries: {str(e)}")

    @staticmethod
    def _extract_urls(query: str) -> list[dict]:
        """
        Uses Serpapi to extract urls from single query.
        """
        params = {
            "engine": "google",
            "q": query,
            "location": "Sydney, New South Wales, Australia",
            "hl": "en",
            "gl": "au",
            "google_domain": "google.com.au",
            "num": "100",
            "start": "0",
            "safe": "active",
            "api_key": settings.serp_api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        return results.get("organic_results", [])

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
                    # Create a new SerpQueries record
                    query_record = SerpQueries(
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
        1. first generate the urls using _extract_urls
        2. then save urls to serp_urls table
        """
        try:
            with db_service.get_session() as session:
                all_urls = []

                # STEP 1: Collect all generated urls first using _extract_urls
                for query in queries:
                    # extract the urls using Serpapi
                    serp_object = self._extract_urls(query)
                    for serp_result in serp_object:
                        all_urls.append({
                            'project_id': project_id,
                            'query': query,
                            'title': serp_result.get('title'),
                            'link': serp_result.get('link'),
                            'snippet': serp_result.get('snippet'),
                            'source': serp_result.get('source')
                        })

                # Step 2: Batch upsert using SQLAlchemy core
                statement = insert(SerpUrls).values(all_urls)
                statement = statement.on_conflict_do_update(
                    index_elements=['link'],
                    set_=dict(
                        title=statement.excluded.title,
                        snippet=statement.excluded.snippet,
                        source=statement.excluded.source
                    )
                )
                session.execute(statement)
                session.commit()
                logging.info(f"✅ Processed {len(all_urls)} URLs for {len(queries)} queries")
            
            return True
                
        except Exception as e:
            logging.error(f"❌ Error saving queries to database: {str(e)}")
            # Check if it's a foreign key violation
            if "ForeignKeyViolation" in str(e):
                raise ValueError(f"Project with ID {project_id} does not exist. Please create the project first.")
            raise
                
# Global project service instance
leads_serp_service = LeadsSerpService()

if __name__ == "__main__":
    #print(leads_serp_service.generate_search_queries("Best sushi stores in Australia")[0])
    #print(leads_serp_service._extract_urls("Best sushi stores in Australia")
    # print(leads_serp_service.add_queries_to_table(3, ["What is a dog","Pizza?"]))
    print(leads_serp_service.generate_and_add_urls_to_table(3, ["What is a dog","Pizza?"]))
"""