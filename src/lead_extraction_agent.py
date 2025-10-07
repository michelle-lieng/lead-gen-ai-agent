from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
import asyncio
import re
import logging
import requests
import os

load_dotenv()

# --- Configure logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
# filter logs so only show when WARNING or higher
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class LeadExtractionAgent:
    
    def __init__(self, client: OpenAI = None):
        self.client = client if client else OpenAI()
    
    @staticmethod
    @function_tool
    def scrape_url(url: str) -> str:
        """
        This tool scrapes the url provided and returns a string of the website scraped.
        Use this tool when the search result seems to provide relevant leads e.g. 
        "Top 100 environmental companies" and you need more information than what is provided in the
        snippet and title to extract leads.
        """
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
        "Authorization": f"Bearer jina_{os.getenv('JINA_API_KEY')}",
        "X-Md-Link-Style": "discarded",
        "X-Remove-Selector": "header, footer, nav, aside, .subscribe, .paywall, .related, .comments, .share, .advertisement",
        "X-Retain-Images": "none"
        }
        logging.info(f"Scraping URL: {url}")
        response = requests.get(jina_url, headers=headers)
        logging.info(f"Scrape status code: {response.status_code}")
        return response.text

    @staticmethod
    def system_prompt():
        return f"""
                You are an AI assistant helping a sustainability organisation (Seabin Foundation) discover **potential corporate partners/leads that take real environmental or sustainability action**.

                Your task:

                1. **Analyse the Google search result** (query, title, snippet).
                2. Decide if the result is likely to list or mention **genuinely sustainability-focused companies**:
                - Companies with clear environmental initiatives, ESG reports, renewable energy adoption, ocean/river cleanup, waste reduction, decarbonisation, etc.
                - Avoid companies only mentioned in a negative context (e.g., "most polluting", "greenwashing", "biggest carbon emitters").
                3. **If the result is relevant and contains company names in the snippet/title → extract them directly.**
                4. **If the result is relevant but the snippet/title doesn’t contain enough names → call the `scrape_url` tool** to load the page and then extract company names.
                5. **If the result is irrelevant or is about polluters/greenwashing rankings or does not align with sustainability partnerships → return an empty list and DO NOT call `scrape_url`.**

                Important rules:**
                - Only return **specific company names** (legal entity names such as “Orica”, “Acciona Energy”, “BHP Group”).
                - Do **not** return industries, sectors, general terms (e.g., “renewable energy companies”, “the mining industry”) or trade groups.
                - Do **not** return product names or government agencies.

                Output:
                - Always return **a valid Python list of company names**: e.g. `["Company A", "Company B"]`.
                - If no suitable companies: return `[]`.
                """
    
    async def lead_extractor(self, query, title, snippet, url) -> tuple[list, str | None]:
        agent = Agent(
            name="Lead Generator",
            instructions=self.system_prompt(),
            tools=[self.scrape_url],
            output_type=List[str], # Specify the output type as a list of strings
        )

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

                # clean scraped content
                if scraped_content:
                    # remove newlines + normalise spaces + strip weird bytes
                    scraped_content = re.sub(r'[\r\n]+', ' ', scraped_content)
                    scraped_content = re.sub(r'\s+', ' ', scraped_content).strip()
                    scraped_content = scraped_content.encode("utf-8", "ignore").decode("utf-8")
                logging.info("Tool output (scraped content) found.")
        logging.info(f"Final output (company names): {result.final_output}")
        # enforce list type for leads
        leads = result.final_output
        return leads, scraped_content

if __name__ == "__main__":
    lead_agent = LeadExtractionAgent()

    # CASE 1: Easy company extraction
    # query = "what are the top environmental corporates in australia"
    # title = "Orica crowned Australia’s most sustainable company for Impact"
    # snippet = "Orica's success this year follows Acconia, an infrastucture and renewable..."
    # url = "https://www.afr.com/companies/mining/orica-crowned-australia-s-most-sustainable-company-for-impact-20240625-p5jojc"

    # CASE 2: Need to scrape
    query = "what are the top environmental corporates in australia"
    title = "crowned Australia’s most sustainable company for Impact"
    snippet = "an infrastucture and renewable..."
    url = "https://www.afr.com/companies/mining/orica-crowned-australia-s-most-sustainable-company-for-impact-20240625-p5jojc"

    # CASE 3: Should return empty list
    # query = "what are the top environmental corporates in australia"
    # title = "Top 14 Most Polluting Companies in 2023"
    # url = "https://www.theecoexperts.co.uk"
    # snippet = "5 June 2025 — The Top 10 Most Polluting Companies · 1. Saudi Aramco · 2. Chevron · 3. Gazprom · 4. ExxonMobil · 5. National Iranian Oil Company (NIOC) · 6. BP · 7."

    final_output, scraped_content = asyncio.run(lead_agent.lead_extractor(query, title, snippet, url))
    print(scraped_content)
    print(final_output)
