"""
note: need to do both pip install serapi and pip install google-search-results for it to work

refer to: https://github.com/serpapi/google-search-results-python
"""
from pprint import pprint
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import json

load_dotenv()

params = {
  "engine": "google",
  "q": "top environmental corporates in australia",
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

with open("learning/output.json", "w") as f:
    json.dump(results, f, indent=4)
# pprint(results)

# organic_results = results["organic_results"]
# pprint(organic_results)