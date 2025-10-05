from agents import Agent, Runner, function_tool
import asyncio
from dotenv import load_dotenv
from pprint import pprint
import json
load_dotenv()


import requests
from dotenv import load_dotenv
import os

load_dotenv()

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

    response = requests.get(jina_url, headers=headers)
    return response.text

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
query = "what are the top environmental corporates in australia"
title = "Top 14 Most Polluting Companies in 2023"
url = "https://www.theecoexperts.co.uk"
snippet = "5 June 2025 — The Top 10 Most Polluting Companies · 1. Saudi Aramco · 2. Chevron · 3. Gazprom · 4. ExxonMobil · 5. National Iranian Oil Company (NIOC) · 6. BP · 7."

prompt = f"""
        You are an AI assistant helping a sustainability company (Seabin Foundation) find potential corporate leads.

        Your task:
        - Read the following Google search result (query, title, snippet).
        - Extract all company names that could be potential leads for Seabin's sustainability initiative.
        - Only include company names that are relevant to sustainability or environmental action.
        - If search result seems irrelevant e.g. companies that are not sustainable, return an empty list.
        - If you cannot extract any company names directly from the snippet and title, and the search result appears relevant, call the "scrape_url" tool with the URL from the search result.

        Return your answer as a Python list of strings, e.g. ["Company A", "Company B"]
        """

agent = Agent(
    name="Lead Generator",
    instructions=prompt,
    tools=[scrape_url],
)

async def main():
    result = await Runner.run(agent, 
                              input=f"""
                                Search Result:
                                Query: {query}
                                Title: {title}
                                Snippet: {snippet}
                                URL: {url}
                              """)
    
    #pprint(result)
    # from pprint import pformat

    # with open("learning/openai_agent_full_output.txt", "w", encoding="utf-8") as f:
    #     f.write(pformat(result))

    print("\n\n-------------------THIS IS THE TOOL OUTPUT---------------------------")
    for item in result.new_items:
        if getattr(item, "type", None) == "tool_call_output_item":
            scraped_content = getattr(item, "output", None)
            print(scraped_content)
    print("\n\n-------------------THIS IS THE FINAL ANSWER---------------------------")
    print(result.final_output)

asyncio.run(main())