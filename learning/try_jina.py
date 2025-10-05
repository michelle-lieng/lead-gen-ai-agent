import requests
from dotenv import load_dotenv
import os

load_dotenv()

url = "https://r.jina.ai/https://www.afr.com/companies/mining/orica-crowned-australia-s-most-sustainable-company-for-impact-20240625-p5jojc"
headers = {
    "Authorization": f"Bearer jina_{os.getenv('JINA_API_KEY')}",
    "X-Md-Link-Style": "discarded",
    "X-Remove-Selector": "header, footer, nav, aside, .subscribe, .paywall, .related, .comments, .share, .advertisement",
    "X-Retain-Images": "none"
}

response = requests.get(url, headers=headers)
print(response.text)