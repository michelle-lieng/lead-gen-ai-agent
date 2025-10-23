
"""
Lead generation from search using AI-powered query generation
"""
from openai import OpenAI
from pydantic import BaseModel

import os
from typing import List
from ..config import settings

class Queries(BaseModel):
    queries: list[str]

def generate_search_queries(description: str, num_queries: int = 5) -> List[str]:
    """
    Generate AI-powered search queries based on project description using ChatGPT
    
    Args:
        description (str): Project description to base queries on
        num_queries (int): Number of queries to generate (default: 5)
    
    Returns:
        List[str]: List of generated search queries
    """
    try:
        # Set OpenAI API key
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        client = OpenAI(api_key=settings.openai_api_key)
        
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
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": "You are an expert at generating targeted search queries for lead generation. Generate precise, effective search queries that will find relevant companies."},
                {"role": "user", "content": prompt}
            ],
            text_format=Queries,
            temperature=0.2
        )
        
        # Parse the response
        queries_object = response.output_parsed
        
        return queries_object.queries #returns a list
        
    except Exception as e:
        print(f"Error generating search queries: {str(e)}")

if __name__ == "__main__":
    print(generate_search_queries("Best sushi stores in Australia")[0])
