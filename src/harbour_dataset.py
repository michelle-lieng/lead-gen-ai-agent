import requests
from .settings import load_settings
import os
import json

load_settings()

location = "-33.8523341,151.2106085"
radius = 2000 # meters

url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
params = {
    "key": os.getenv("GOOGLE_MAPS_API_KEY"),
    "location": location,
    "radius": radius,
    "rankby": "prominence",
    "type": "establishment"
}

response = requests.get(url, params=params)
businesses = response.json()["results"]


print(businesses)
with open(r"src\harbour_businesses", "w") as f:
    json.dump(businesses, f, indent=4) # indent for pretty-printing (optional)
