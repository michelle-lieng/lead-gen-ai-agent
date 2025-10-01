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

cur.close()
conn.close()
