
"""
Lead generation from search using AI-powered query generation
"""
from openai import OpenAI
from pydantic import BaseModel
import os
from typing import List
from serpapi import GoogleSearch

from ..config import settings
from .database import db_service
from ..models.tables import Queries
from ..models.schemas import QueryListRequest

class GenerateLeadsFromSearch:
    """Service for generating leads from search operations"""
    
    def __init__(self):
        """Initialise leads from search service with database service"""
        self.db = db_service
        # Initialize OpenAI client once
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def generate_search_queries(self, description: str, num_queries: int = 2) -> List[str]:
        """
        Generate AI-powered search queries based on project description using ChatGPT
        
        Args:
            description (str): Project description to base queries on
            num_queries (int): Number of queries to generate (default: 5)
        
        Returns:
            List[str]: List of generated search queries
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
            print(f"Error generating search queries: {str(e)}")

    @staticmethod
    def extract_initial_urls(queries: list) -> List[dict]:
        all_extracted_urls = []
        for query in queries:
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
            all_extracted_urls += results.get("organic_results", [])
        return all_extracted_urls

    def add_queries_to_table(self, project_id: int, queries: List[str]) -> bool:
        """
        Save generated search queries to the database for a specific project.
        
        Args:
            project_id (int): ID of the project these queries belong to
            queries (List[str]): List of search queries to save
        
        Returns:
            bool: shows if successiveful or not
        """
        try:
            with self.db.get_session() as session:
                for query in queries:
                    # Create a new Queries record
                    query_record = Queries(
                        project_id=project_id,
                        query=query
                    )
                    session.add(query_record)
                
                # Commit all queries at once
                session.commit()
                
                return True
                
        except Exception as e:
            print(f"❌ Error saving queries to database: {str(e)}")
            raise

    def add_initial_urls_to_table():
        pass

if __name__ == "__main__":
    generate_leads = GenerateLeadsFromSearch()
    #print(generate_search_queries("Best sushi stores in Australia")[0])
    #print(extract_initial_urls(["Best sushi stores in Australia", "Cats"]))
    print(generate_leads.add_queries_to_table(3, ["What is a dog","Pizza?"]))
"""