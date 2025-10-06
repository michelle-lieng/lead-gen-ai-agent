"""
Main file where AI Lead Gen runs
"""
import asyncio
from dotenv import load_dotenv
import yaml
import logging

from DatabaseManager import DatabaseManager
from SerpAPIManager import SerpAPIManager
from InitialLeadAgent import InitialLeadAgent

# Load variables
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

load_dotenv()

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class AILeadGenerator():
    DatabaseManager = DatabaseManager()
    SerpAPIManager = SerpAPIManager()
    InitialLeadAgent = InitialLeadAgent()

    def __init__(self):
        pass

    def setup(self):
        """
        Here we connect to db and set up all the tables.
        """
        # connect to db set in config
        self.DatabaseManager.connect_to_db()

        # create all tables in db if not already exist
        self.DatabaseManager.create_tables()
    
    def collect_initial_urls(self, queries: list):
        """
        Step 1 of the AI lead gen. 
        
        Given a list of queries loop through each query and 
        for each pull 100 results and feed into
        the postgres table: "initial_urls".
        """
        for query in queries:
            # serpapi_results = self.SerpAPIManager.call_api(query=query)
            # temporary to save api costs
            serpapi_results = self.SerpAPIManager.load_from_json()
            self.DatabaseManager.upsert_initial_urls(
                query=query,
                serpapi_results=serpapi_results
            )

    async def collect_initial_leads(self):
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
        rows = self.DatabaseManager.fetch_unprocessed_urls()
        
        # run all lead_extractor calls in parallel
        tasks = [
            self.InitialLeadAgent.lead_extractor(query, title, snippet, link)
            for (row_id, query, title, link, snippet) in rows
        ]
        results = await asyncio.gather(*tasks)

        for (row_id, _, _, _, _), (leads, scraped) in zip(rows, results):
            self.DatabaseManager.upsert_leads(row_id, leads, scraped)

    def end_lead_gen(self):
        """
        Save DB and close connection to DB.
        """
        self.DatabaseManager.download_csv()
        self.DatabaseManager.close()

    async def main(self):
        # 1. Connect to db + create tables
        self.setup()

        # 2. Collect all initial google search results from query
        queries = ["what are the top environmental corporates in australia"]
        self.collect_initial_urls(queries)

        # 3. For each search result we take the title, URL, snippet and query and extract leads
        await self.collect_initial_leads()

        # End step: Save all DB and close connection
        self.end_lead_gen()

if __name__ == "__main__":
    AILeadGenerator = AILeadGenerator()
    asyncio.run(AILeadGenerator.main())

        