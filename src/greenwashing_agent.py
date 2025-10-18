import requests
from .settings import load_settings
import os
import json
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel, Field

load_settings()

# Define the output schema using Pydantic
class GreenwashingAnalysis(BaseModel):
    is_greenwashing: bool = Field(description="Whether the company is engaging in greenwashing")
    greenwashing_key_evidence: list[str] = Field(description="Key evidence supporting the greenwashing determination")
    greenwashing_reasoning: str = Field(description="Brief explanation of the decision")

# lead_to_enrich = "arup"

# url = 'https://s.jina.ai/'
# params = {'q': f'{lead_to_enrich} company greenwashing', 'gl': 'AU', 'location': 'Sydney', 'hl': 'en'}
# headers = {
#     'Accept': 'application/json',
#     'Authorization': f'Bearer jina_{os.getenv("JINA_API_KEY")}',
#     'X-Respond-With': 'no-content'
# }

# response = requests.get(url, params=params, headers=headers)

# # Parse the JSON string and save with proper indentation
# data = json.loads(response.text)
# with open('src/greenwashing_output.json', 'w') as f:
#     json.dump(data, f, indent=2)

with open('src/greenwashing_output.json','r') as f:
    scraped_data = json.load(f)
# More concise approach using list comprehension
def parse_date(date_str):
    """Parse date with multiple format support"""
    for fmt in ["%d %b %Y", "%d %B %Y"]:  # Try both formats
        try:
            return datetime.strptime(date_str, fmt).year
        except ValueError:
            continue
    return None

# Filter articles from 2020 onwards in one line
relevant_greenwashing_articles = [
    article for article in scraped_data['data'] 
    if article.get('date') and (year := parse_date(article['date'])) and year >= 2020
]

# Save formatted articles for LLM input
formatted_articles = []
for article in relevant_greenwashing_articles:
    formatted_text = f"Article title: {article['title']} - Article description: {article['description']}"
    formatted_articles.append(formatted_text)
    print(formatted_text)

# Save to file for LLM processing
with open('src/formatted_greenwashing_articles.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(formatted_articles))

print(f"\nSaved {len(formatted_articles)} articles to 'src/formatted_greenwashing_articles.txt'")

client = OpenAI()

# Read the formatted articles for context
with open('src/formatted_greenwashing_articles.txt', 'r', encoding='utf-8') as f:
    articles_context = f.read()

# Search-based greenwashing detection prompt
prompt = f"""
You are analyzing EXTERNAL articles (not written by the company) that were found by searching for "greenwashing + [company name]". Your task is to determine if these search results actually contain greenwashing allegations against the company.

TASK:
Based on the search results, determine:
1. Do these articles contain actual greenwashing allegations against the company? (True/False)
2. Are these articles directly about the company's greenwashing practices? (True/False)

WHAT TO LOOK FOR:
- Articles that specifically accuse the company of greenwashing
- Regulatory complaints or investigations about the company's environmental claims
- News reports about the company being caught in misleading environmental advertising
- Legal actions against the company for false environmental claims
- Journalistic investigations exposing the company's deceptive practices

ANALYSIS APPROACH:
1. Check if articles contain specific greenwashing allegations against the company
2. Look for regulatory actions, complaints, or legal cases
3. Identify news reports about the company being caught in deceptive practices
4. Determine if the articles are about actual greenwashing scandals, not general sustainability efforts

IMPORTANT: You are NOT analyzing the company's own communications. You are analyzing whether external sources have accused the company of greenwashing. If the search results don't contain specific allegations, complaints, or investigations about greenwashing, then the answer should be False.
"""

# Make the API call with structured output
response = client.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": f"You are an expert environmental analyst. Your job is to determine if articles found by searching 'greenwashing + company name' are actually about greenwashing allegations against that company. CONTEXT - These are EXTERNAL articles (not written by the company) found by searching for greenwashing about this company:{articles_context}"},
        {"role": "user", "content": prompt}
    ],
    response_format=GreenwashingAnalysis,
    temperature=0.1
)

# Get the parsed result
result = response.choices[0].message.parsed
print(f"Greenwashing: {result.is_greenwashing}")
print(f"Key Evidence: {result.greenwashing_key_evidence}")
print(f"Reasoning: {result.greenwashing_reasoning}")

# Save to file
with open('src/greenwashing_analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(result.model_dump(), f, indent=2)