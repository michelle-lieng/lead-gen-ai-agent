# STEP 1: USER HAS A SCOPE + WRITES IT OUT 
# FOR NOW USER WILL GENERATE 1 QUESTION TO SEARCH 
# WE WILL GET 100 RESULTS AND SAVE INTO POSTGRESQL TABLE

from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import json
import psycopg2
from dotenv import load_dotenv
import os
import yaml
import logging
import sys
from openai import OpenAI
from dotenv import load_dotenv
from DatabaseManager import DatabaseManager
from SerpApiManager import SerpApiManager
from LLMManager import LLMManager

# Load variables
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

load_dotenv()

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,           # can be DEBUG/INFO/WARNING/ERROR
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class AILeadGenerator():
    db = DatabaseManager()
    sm = SerpApiManager()
    lm = LLMManager()

    def __init__(self):
        pass

    def setup(self):
        """
        Here we connect to db and set up all the tables.
        """
        # connect to db set in config
        self.db.connect_to_db()

        # create all tables in db if not already exist
        self.db.create_tables()
    
    def collect_initial_urls(self, queries: list):
        """
        Step 1 of the AI lead gen. 
        
        Given a list of queries loop through each query and 
        for each pull 100 results and feed into
        the postgres table: "initial_urls".
        """
        for query in queries:
            # serpapi_results = self.sm.call_api(query=query)
            # temporary to save api costs
            serpapi_results = self.sm.load_from_json()
            self.db.upsert_initial_urls(
                query=query,
                serpapi_results=serpapi_results
            )

    def collect_initial_leads(self):
        """
        Step 2 of AI Lead gen.

        Now that "initial_urls" table has been populated
        we go down each row and extract the title, url, snippet
        and query and ask an AI Agent to:
        1. If it can extract leads from snippet does so.
        2. If it needs more info scrapes the url and extracts leads.
        3. If it sees the page is not aligned to the profile we want
        to extract skip.
        
        Will update status of "initial_urls" from "unprocessed" to 
        "processed" or "skip" and if it scrapes a page then 
        will update the "website_scraped" column. 

        Will update the "leads" table.
        """
        rows = self.db.fetch_unprocessed_urls()
        for row in rows:
            row_id, query, title, link, snippet = row
            final_output, scraped_content = self.lm.lead_extractor(query, title, snippet, link)
            self.db.upsert_leads(row_id, final_output, scraped_content)

    def close_connection(self):
        self.db.close()

    def main(self):
        # First connect to db + create tables
        self.setup()
        queries = ["what are the top environmental corporates in australia"]
        self.collect_initial_urls(queries)
        self.collect_initial_leads()
        self.close_connection()

if __name__ == "__main__":
    alg = AILeadGenerator()
    alg.main()

        