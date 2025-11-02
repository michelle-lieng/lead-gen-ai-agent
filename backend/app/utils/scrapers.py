"""
Jina Scrapers
1. For scraping URL
2. For scraping SERP 

Note: They all cache content.
"""
import requests
import json
import ast
import re
import unicodedata

from ..config import settings

def clean_content(content: str) -> str:
    """
    Clean scraped content by removing weird characters, excessive whitespace, and formatting issues.
    """
    if not content:
        return content
    
    # Remove excessive dashes and separators
    content = re.sub(r'-{10,}', '', content)  # Remove 10+ consecutive dashes
    content = re.sub(r'={10,}', '', content)  # Remove 10+ consecutive equals
    content = re.sub(r'_{10,}', '', content)  # Remove 10+ consecutive underscores
    content = re.sub(r'\.{10,}', '', content)  # Remove 10+ consecutive dots
    
    # Remove weird Unicode characters and control characters
    content = re.sub(r'[\u200b-\u200d\ufeff]', '', content)  # Remove zero-width characters
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)  # Remove control characters (includes null bytes)
    
    # Normalize Unicode characters (convert to decomposed form)
    content = unicodedata.normalize('NFKD', content)
    
    # Remove all newlines and carriage returns, replace with spaces
    content = re.sub(r'[\r\n]+', ' ', content)  # Replace newlines/carriage returns with spaces
    
    # Normalize all whitespace to single spaces and strip
    content = re.sub(r'\s+', ' ', content).strip()
    
    # Clean UTF-8 encoding (removes any invalid UTF-8 sequences)
    content = content.encode("utf-8", "ignore").decode("utf-8")

    # Remove excessive whitespace while preserving paragraph structure [OLD CODE]
    #content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Replace 3+ newlines with 2
    #content = re.sub(r'[ \t]+', ' ', content).strip()  # Replace multiple spaces/tabs with single space
            
    return content

def jina_url_scraper(url: str) -> str:
    """
    Uses jina api to scrape url and clean the content.
    """
    url = f"https://r.jina.ai/{url}"
    headers = {
        #"Authorization": f"Bearer jina_{settings.jina_api_key}",
        "X-Md-Link-Style": "discarded",
        "X-Remove-Selector": "header, footer, nav, aside, .subscribe, .paywall, .related, .comments, .share, .advertisement",
        "X-Retain-Images": "none"
    }
    response = requests.get(url, headers=headers)
    raw_content = response.text
    
    # Clean the scraped content
    cleaned_content = clean_content(raw_content)
    
    return cleaned_content

def jina_serp_scraper(search_phrase:str) -> list[dict]:
    url = 'https://s.jina.ai/'
    params = {'q': f'{search_phrase}', 'gl': 'AU', 'location': 'Sydney', 'hl': 'en'}
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer jina_{settings.jina_api_key}',
        'X-Respond-With': 'no-content'
    }
    response = requests.get(url, params=params, headers=headers)
    return ast.literal_eval(response.text)['data'] # convert to dict then extract data 

if __name__ == "__main__":
    from pprint import pprint
    # try url scraper
    url = "https://www.our-trace.com/blog/23-companies-in-australia-doing-great-things-in-sustainability"
    print(jina_url_scraper(url))

    # try serp scraper
    # search_phrase = "Coles company greenwashing"
    # pprint(jina_serp_scraper(search_phrase))