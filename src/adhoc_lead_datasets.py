"""
We use psycopg2 for everything else (queries, inserts, updates) and SQLAlchemy only for DataFrame uploads.
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from .settings import load_settings
import re

# Load settings
settings, config = load_settings()

# Create connection string
# postgres://user:password@host:port/database
conn_string = f"postgresql+psycopg2://{settings.POSTGRESQL_USER}:{settings.POSTGRESQL_PASSWORD}@{settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}/{config.postgresql_database}?client_encoding=utf8"

# Create SQLAlchemy engine with explicit UTF-8 encoding
engine = create_engine(conn_string)

# Read CSV
df = pd.read_csv(r'lead_datasets\bcorp.csv')
print(f"Original dataset: {len(df)} rows")

# Filter row where country == Australia
df = df[df['country'] == 'Australia']

# was planning to join with main leads table and drop all decertified later
# but want to apply all transformations before joining for code reusability
df = df[df['current_status']=='certified']

print(f"After filtering: {len(df)} rows")

# Select relevant columns
df = df[['company_name', 'description', 'industry', 'industry_category', 
'products_and_services', 'state', 'city', 'sector', 'size', 'b_corp_profile',
'website', 'assessment_year', 'overall_score']]

# Rename overall_score to bcorp_overall_score
df = df.rename(columns={'overall_score': 'bcorp_overall_score'})

# Deduplicate rows 
df = df.drop_duplicates(subset=['company_name'])
print(f"After deduplication: {len(df)} rows")

# Clean up ALL string columns - remove problematic Unicode characters
print("🧹 Cleaning Unicode characters...")
for col in df.columns:
    if df[col].dtype == 'object':  # Only clean string columns
        df[col] = df[col].astype(str).apply(
            lambda x: re.sub(r'[\r\n]+', ' ', x) if pd.notna(x) else x
        )
        df[col] = df[col].astype(str).apply(
            lambda x: re.sub(r'\s+', ' ', x).strip() if pd.notna(x) else x
        )
        # Remove problematic Unicode characters (like 0xe2 0x80 0x8b)
        df[col] = df[col].astype(str).apply(
            lambda x: x.encode("utf-8", "ignore").decode("utf-8") if pd.notna(x) else x
        )
print("✅ Unicode cleaning complete")

try:
    print("🔄 Starting upload...")
    df.to_sql('bcorp_companies', engine, if_exists='replace', index=False)
    print("✅ B Corp data uploaded to PostgreSQL!")

except Exception as e:
    print(f"❌ Upload failed: {e}")

# # let's join with main leads table and drop all decertified later


