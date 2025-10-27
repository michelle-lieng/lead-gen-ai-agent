"""
Jina Scrapers
1. For scraping URL
2. For scraping SERP 

Note: They all cache content.
"""
import requests
import json
import ast

from ..config import settings

def jina_url_scraper(url: str) -> str:
    """
    Uses jina api to scrape url.
    """
    headers = {
        #"Authorization": f"Bearer jina_{settings.jina_api_key}",
        "X-Md-Link-Style": "discarded",
        "X-Remove-Selector": "header, footer, nav, aside, .subscribe, .paywall, .related, .comments, .share, .advertisement",
        "X-Retain-Images": "none"
    }
    response = requests.get(url, headers=headers)
    return response.text

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
    url = "https://r.jina.ai/https://www.afr.com/companies/mining/orica-crowned-australia-s-most-sustainable-company-for-impact-20240625-p5jojc"
    print(jina_url_scraper(url))

    # try serp scraper
    search_phrase = "Coles company greenwashing"
    pprint(jina_serp_scraper(search_phrase))