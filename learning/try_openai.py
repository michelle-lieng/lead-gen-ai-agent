from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

query = "what are the top environmental corporates in australia"
title = "Orica crowned Australia’s most sustainable company for Impact"
snippet = "Orica's success this year follows Acconia, an infrastucture and renewable..."

prompt = f"""
You are an AI assistant helping a sustainability company (Seabin Foundation) find potential corporate leads.

Your task:
- Read the following Google search result (query, title, snippet).
- Extract all company names that could be potential leads for Seabin's sustainability initiative.
- Only include company names that are relevant to sustainability or environmental action.
- If there are no relevant companies, return an empty list.

Return your answer as a Python list of strings, e.g. ["Company A", "Company B"]

Search Result:
Query: {query}
Title: {title}
Snippet: {snippet}

MUST ENSURE OUTPUT IS A PYTHON LIST!
"""

response = client.responses.create(
    model="gpt-3.5-turbo",
    input=prompt
)

print(response.output_text)