"""
This class manages all connections to my postgre db.
"""
import os
import psycopg2
import yaml
import logging
import sys
from pathlib import Path
from datetime import datetime

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,           # can be DEBUG/INFO/WARNING/ERROR
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class DatabaseManager:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)
        self.db_name = self.config.get("postgresql_database")
        if self.db_name is None:
            logging.error("❌ Add database name to config.yaml")
            sys.exit(1)
        self.conn = None #database connection object
        self.cur = None #cursor object to execute SQL commands on connection

    def create_new_db(self):
        # First connect to existing database
        try:
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
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.db_name,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(f'CREATE DATABASE "{self.db_name}";')
            logging.info(f"Database '{self.db_name}' created!")
        else:
            logging.info(f"Database '{self.db_name}' already exists.")

        # Close the initial connection
        cur.close()
        conn.close()
    
    def connect_to_db(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("POSTGRESQL_HOST"),
                port=os.getenv("POSTGRESQL_PORT"),
                database=self.db_name,
                user=os.getenv("POSTGRESQL_USER"),
                password=os.getenv("POSTGRESQL_PASSWORD")
            )
            self.cur = self.conn.cursor()
            logging.info(f"📦 Connected to '{self.db_name}' successfully.")
        except Exception as e:
            logging.error(f"❌ Could not connect to target database: {e}")
            # Attempt to create the DB if missing, then reconnect once.
            self.create_new_db()
            try:
                self.conn = psycopg2.connect(
                    host=os.getenv("POSTGRESQL_HOST"),
                    port=os.getenv("POSTGRESQL_PORT"),
                    database=self.db_name,
                    user=os.getenv("POSTGRESQL_USER"),
                    password=os.getenv("POSTGRESQL_PASSWORD")
                )
                self.cur = self.conn.cursor()
                logging.info(f"📦 Reconnected to '{self.db_name}' successfully after creation.")
            except Exception as re:
                logging.error(f"❌ Reconnect failed after creating database: {re}")
                # Hard exit to avoid None cursor downstream
                sys.exit(1)

    def create_tables(self):
        # create table for initial collection of website urls
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS initial_urls (
            id SERIAL PRIMARY KEY,            -- auto-incrementing unique ID
            query TEXT NOT NULL,              -- original search query
            title TEXT,                       -- title of the result
            link TEXT UNIQUE,                 -- final URL
            snippet TEXT,                     -- snippet/description from search
            source TEXT,                      -- domain or source field
            website_scraped TEXT,
            status TEXT NOT NULL DEFAULT 'unprocessed',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

        # Create leads table if not exists
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            initial_url_id INTEGER REFERENCES initial_urls(id),
            lead TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        self.conn.commit()
        logging.info("✅ Tables ensured.")

    def upsert_initial_urls(self, query: str, serpapi_results: dict):
        rows = 0
        for item in serpapi_results:
            link = item.get("link") or item.get("redirect_link")
            title   = item.get("title")
            snippet = item.get("snippet")
            source  = item.get("source")
            self.cur.execute("""
                INSERT INTO initial_urls (query, title, link, snippet, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (link) DO UPDATE
                SET title    = COALESCE(EXCLUDED.title,   initial_urls.title),
                    snippet  = COALESCE(EXCLUDED.snippet, initial_urls.snippet),
                    source   = COALESCE(EXCLUDED.source,  initial_urls.source)
            """, (query, title, link, snippet, source))
            rows += 1

        self.conn.commit()
        logging.info(f"✅ Upserted {rows} rows for query: {query}")

    def fetch_unprocessed_urls(self):
        self.cur.execute("SELECT id, query, title, link, snippet FROM initial_urls WHERE status = 'unprocessed';")
        return self.cur.fetchall() #these are all the rows we have to go through

    def upsert_leads(self, initial_url_id: int, leads: list, scraped_page: str | None = None):
        if len(leads) == 0:
            self.cur.execute(
                "UPDATE initial_urls SET status = 'no_leads' WHERE id = %s;",
                (initial_url_id,)
            )
        else:
            for lead in leads:
                # create a new row 
                self.cur.execute(
                    "INSERT INTO leads (initial_url_id, lead) VALUES (%s, %s);",
                    (initial_url_id, lead)
                )
                # update status of initial_urls table 
                self.cur.execute(
                    "UPDATE initial_urls SET status = 'processed' WHERE id = %s;",
                    (initial_url_id,)
                )

                if scraped_page is not None:
                    # update webscraped column
                    self.cur.execute(
                        "UPDATE initial_urls SET website_scraped = %s WHERE id = %s;",
                        (scraped_page, initial_url_id)
                    )
                else:
                    # update webscraped column
                    self.cur.execute(
                        "UPDATE initial_urls SET website_scraped = 'no_scrape' WHERE id = %s;",
                        (initial_url_id,)
                    )
                
        self.conn.commit()
    
    def download_csv(self):
        filename_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save under project working directory to keep path portable across OSes
        outdir = Path.cwd() / "output" / self.db_name / filename_ts
        outdir.mkdir(parents=True, exist_ok=True)  # make folder if it doesn’t exist

        # export initial_urls
        with open(outdir / "initial_urls.csv", "w", newline="", encoding="utf-8-sig") as f:
            self.cur.copy_expert(
                "COPY (SELECT * FROM initial_urls) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');",
                f,
            )

        # export leads
        with open(outdir / "leads.csv", "w", newline="", encoding="utf-8-sig") as f:
            self.cur.copy_expert(
                "COPY (SELECT * FROM leads) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');",
                f,
            )

        self.conn.commit()
        logging.info(f"✅ CSVs saved to {outdir}")

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    DatabaseManager = DatabaseManager()
    DatabaseManager.connect_to_db()
    DatabaseManager.download_csv()