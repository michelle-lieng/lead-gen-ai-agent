# STEP 1: USER HAS A SCOPE + WRITES IT OUT 
# FOR NOW USER WILL GENERATE 1 QUESTION TO SEARCH 
# WE WILL GET 100 RESULTS AND SAVE INTO POSTGRESQL TABLE

from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import json
import psycopg2
from dotenv import load_dotenv
import os
import yaml
import logging
import sys

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,           # can be DEBUG/INFO/WARNING/ERROR
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Load variables
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)
load_dotenv()

# add logging here if database is none
DB_NAME = config.get("postgresql_database")
if DB_NAME is None:
    logging.error(f"❌ Add database name to config.yaml")
    sys.exit(1)

try:
    # Connect to existing database
    conn = psycopg2.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=os.getenv("POSTGRESQL_PORT"),
        database=os.getenv("POSTGRESQL_INITIAL_DATABASE"),     # connect to postgres default DB first
        user=os.getenv("POSTGRESQL_USER"),         # user that has CREATEDB or SUPERUSER
        password=os.getenv("POSTGRESQL_PASSWORD")
    )
    logging.info("✅ Connected to PostgreSQL successfully.")

except psycopg2.OperationalError as e:
    logging.error(f"❌ Could not connect to PostgreSQL: {e}")
    sys.exit(1)

except Exception as e:
    logging.exception("❌ Unexpected error occurred while connecting to PostgreSQL")
    sys.exit(1)

conn.autocommit = True  # CREATE DATABASE can't be in a transaction
cur = conn.cursor()

# Check if the database already exists
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
exists = cur.fetchone()

if not exists:
    cur.execute(f'CREATE DATABASE "{DB_NAME}";')
    print(f"Database '{DB_NAME}' created!")
else:
    print(f"Database '{DB_NAME}' already exists.")

# Close the initial connection
cur.close()
conn.close()

# ---- 🔥 Now connect to the new database ----
conn2 = psycopg2.connect(
    host=os.getenv("POSTGRESQL_HOST"),
    port=os.getenv("POSTGRESQL_PORT"),
    database=DB_NAME,
    user=os.getenv("POSTGRESQL_USER"),
    password=os.getenv("POSTGRESQL_PASSWORD")
)
cur2 = conn2.cursor()

# create table for initial collection of website urls
cur2.execute("""
CREATE TABLE IF NOT EXISTS serpapi_urls (
    id SERIAL PRIMARY KEY,            -- auto-incrementing unique ID
    query TEXT NOT NULL,              -- original search query
    title TEXT,                       -- title of the result
    link TEXT UNIQUE,                        -- final URL
    snippet TEXT,                     -- snippet/description from search
    source TEXT                      -- domain or source field
);
""")
conn2.commit()

print(f"📦 Connected to '{DB_NAME}' and created table successfully.")

# load_dotenv()
query = "what are the top environmental corporates in australia"
# params = {
#   "engine": "google",
#   "q": query,
#   "location": "Sydney, New South Wales, Australia",
#   "hl": "en",
#   "gl": "au",
#   "google_domain": "google.com.au",
#   "num": "100",
#   "start": "0",
#   "safe": "active",
#   "api_key": os.getenv("SERP_API_KEY")
# }

# search = GoogleSearch(params)
# results = search.get_dict()

import json 
with open('learning/output.json', 'r') as f:
    # Load the JSON data from the file
    results = json.load(f)
organic = results.get("organic_results", [])
rows = 0

for item in organic:
    link = item.get("link") or item.get("redirect_link")
    title   = item.get("title")
    snippet = item.get("snippet")
    source  = item.get("source")

    cur2.execute("""
        INSERT INTO serpapi_urls (query, title, link, snippet, source)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (link) DO UPDATE
          SET title    = COALESCE(EXCLUDED.title,   serpapi_urls.title),
              snippet  = COALESCE(EXCLUDED.snippet, serpapi_urls.snippet),
              source   = COALESCE(EXCLUDED.source,  serpapi_urls.source)
    """, (query, title, link, snippet, source))
    rows += 1

conn2.commit()
logging.info(f"✅ Upserted {rows} rows for query: {query}")

cur2.close()
conn2.close()