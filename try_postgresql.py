import psycopg2
from dotenv import load_dotenv
import os
import yaml
import logging

# Load config.yaml
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# add logging here if database is none
DB_NAME = config.get("postgresql_database")


load_dotenv()

# Connect to an existing database
conn = psycopg2.connect(
    host=os.getenv("POSTGRESQL_HOST"),
    port=os.getenv("POSTGRESQL_PORT"),
    database=os.getenv("POSTGRESQL_INITIAL_DATABASE"),     # connect to postgres default DB first
    user=os.getenv("POSTGRESQL_USER"),         # user that has CREATEDB or SUPERUSER
    password=os.getenv("POSTGRESQL_PASSWORD")
)

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
