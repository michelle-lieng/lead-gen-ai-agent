import requests
from .settings import load_settings
import os
import json
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel, Field

load_settings()

# Define the output schema using Pydantic
class SustainabilityAnalysis(BaseModel):
    is_sustainability_focused: bool = Field(description="Whether the company demonstrates genuine sustainability commitment")
    sustainability_key_evidence: list[str] = Field(description="Key evidence supporting the sustainability determination")
    sustainability_reasoning: str = Field(description="Brief explanation of the decision")

# #Example usage for testing (uncomment to test with a specific company)
# lead_to_enrich = "Stockinette Bags Pallet Freezer Spacers"

# url = 'https://s.jina.ai/'
# params = {'q': f'{lead_to_enrich} company sustainability practices environmental impact', 'gl': 'AU', 'location': 'Sydney', 'hl': 'en'}
# headers = {
#     'Accept': 'application/json',
#     'Authorization': f'Bearer jina_{os.getenv("JINA_API_KEY")}',
#     'X-Respond-With': 'no-content'
# }

# response = requests.get(url, params=params, headers=headers)

# # Parse the JSON string and save with proper indentation
# data = json.loads(response.text)
# with open('src/sustainability_output.json', 'w') as f:
#     json.dump(data, f, indent=2)

# Load existing sustainability data (replace with actual API call in production)
with open('src/sustainability_output.json','r') as f:
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
relevant_sustainability_articles = [
    article for article in scraped_data['data'] 
    if article.get('date') and (year := parse_date(article['date'])) and year >= 2020
]

# Save formatted articles for LLM input
formatted_articles = []
for article in relevant_sustainability_articles:
    formatted_text = f"Article title: {article['title']} - Article description: {article['description']}"
    formatted_articles.append(formatted_text)
    print(formatted_text)

# Save to file for LLM processing
with open('src/formatted_sustainability_articles.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(formatted_articles))

print(f"\nSaved {len(formatted_articles)} articles to 'src/formatted_sustainability_articles.txt'")

client = OpenAI()

# Read the formatted articles for context
with open('src/formatted_sustainability_articles.txt', 'r', encoding='utf-8') as f:
    articles_context = f.read()

# Comprehensive sustainability assessment prompt
prompt = f"""
You are analyzing articles about a company's sustainability practices and environmental impact. Your task is to determine if the company demonstrates genuine sustainability commitment beyond just mentioning sustainability in passing.

TASK:
Based on the search results, determine:
1. Does the company demonstrate genuine sustainability commitment? (True/False)
2. Is there substantial evidence of concrete sustainability actions and measurable impact? (True/False)

WHAT TO LOOK FOR - POSITIVE INDICATORS:
- Specific sustainability goals with measurable targets and timelines
- Third-party certifications (B Corp, LEED, ISO 14001, etc.)
- Detailed sustainability reports with metrics and progress tracking
- Concrete environmental initiatives with quantifiable results
- Investment in renewable energy, waste reduction, carbon footprint reduction
- Supply chain sustainability programs
- Employee sustainability programs
- Community environmental initiatives
- Awards or recognition for sustainability efforts
- Partnerships with environmental organizations
- Transparent reporting on environmental impact

WHAT TO LOOK FOR - NEGATIVE INDICATORS:
- Vague or generic sustainability statements without specifics
- Greenwashing allegations or controversies
- Lack of measurable goals or progress tracking
- Minimal environmental impact despite sustainability claims
- No third-party verification of claims
- Contradictory practices (e.g., claiming sustainability while having poor environmental record)
- Lack of transparency in sustainability reporting

ANALYSIS APPROACH:
1. Look for concrete, measurable sustainability actions
2. Check for third-party verification and certifications
3. Assess the depth and specificity of sustainability initiatives
4. Evaluate transparency and reporting quality
5. Consider the company's overall environmental impact and track record
6. Look for evidence of genuine commitment vs. superficial mentions

IMPORTANT: A company cannot be considered sustainability-focused if it only mentions sustainability in passing or has vague, unsubstantiated claims. Look for substantial evidence of concrete actions, measurable impact, and genuine commitment to environmental responsibility.

For the key evidence, provide direct quotes from the articles that support your determination.
"""

# Make the API call with structured output
response = client.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": f"You are an expert sustainability analyst. Your job is to determine if a company demonstrates genuine sustainability commitment based on concrete evidence and measurable actions. CONTEXT - These are articles about the company's sustainability practices:{articles_context}"},
        {"role": "user", "content": prompt}
    ],
    response_format=SustainabilityAnalysis,
    temperature=0.1
)

# Get the parsed result
result = response.choices[0].message.parsed
print(f"Sustainability Focused: {result.is_sustainability_focused}")
print(f"Key Evidence: {result.sustainability_key_evidence}")
print(f"Reasoning: {result.sustainability_reasoning}")

# Save to file
with open('src/sustainability_analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(result.model_dump(), f, indent=2)
