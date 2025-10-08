import json
import os
from serpapi import GoogleSearch

class SerpAPIManager:
    def __init__(self):
        pass

    def call_api(self, query: str) -> dict:
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
        "api_key": os.getenv("SERP_API_KEY")
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        return results.get("organic_results", [])
    
    def load_from_json(self, 
                       json_path: str = 'fixtures/serpapi_example_output.json') -> dict:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except FileNotFoundError:
            import logging
            logging.warning(f"Fixture not found at {json_path}; returning empty results.")
            return []
        return results.get("organic_results", [])

if __name__ == "__main__":
    search = SerpAPIManager()
    print(search.load_from_json())
