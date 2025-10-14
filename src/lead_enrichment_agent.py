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

# Comprehensive prompt with all necessary instructions
prompt = f"""
You are an expert environmental analyst tasked with determining if a company is engaging in greenwashing based on news articles and evidence.

TASK:
Analyze the provided articles and determine:
1. Is the company engaging in greenwashing? (True/False)
2. Are these articles relevant to the specific company? (True/False)

GREENWASHING INDICATORS to look for:
- Misleading environmental claims
- Exaggerated sustainability efforts
- False or deceptive advertising about environmental impact
- Regulatory violations or complaints
- Discrepancy between public claims and actual practices
- Use of vague or unsubstantiated environmental language

RELEVANCE CRITERIA:
- Articles must specifically mention the company by name
- Content must be directly related to the company's environmental practices
- Recent articles (2020+) are more relevant than older ones

ANALYSIS STEPS:
1. Read through each article carefully
2. Identify specific claims or allegations against the company
3. Look for regulatory actions, complaints, or investigations
4. Assess the credibility and recency of the sources
5. Determine if the evidence supports a greenwashing conclusion
6. Evaluate if the articles are directly relevant to the company

IMPORTANT: Only consider articles that are directly relevant to the specific company. If articles are not about the company or are about different companies, they should not influence your greenwashing assessment.
"""

# Make the API call with structured output
response = client.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": f"You are an expert environmental analyst specializing in greenwashing detection. CONTEXT - Recent articles about the company:{articles_context}"},
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