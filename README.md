# Lead Gen AI Agent

An AI-powered lead generation platform that discovers and enriches potential corporate partners through intelligent search and analysis. Built with FastAPI, Streamlit, and OpenAI.

## 🎬 Demo

[Watch the Demo](https://www.youtube.com/watch?v=ChB0G_PbmNI)

## 🚀 Features

- **AI-Powered Search**: Automatically generates search queries and extracts company names
- **Lead Enrichment**: Analyzes companies for specific attributes (e.g., environmental reports, sustainability)
- **Dataset Management**: Upload and merge CSV datasets with discovered leads
- **Project Organization**: Organize leads by projects with stats

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 12+
- OpenAI API key
- Jina API key

## 🛠️ Installation

1. **Clone and install dependencies:**
```bash
git clone <repository-url>
cd lead-gen-ai-agent
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your API keys and database credentials
```

3. **Create database:**
Create a new database named `ai_lead_generator` (I used psql)

*Note: The backend will automatically create all required tables when it starts.*

## 🚀 Quick Start

**Start the backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Start the frontend:**
```bash
cd frontend
streamlit run app.py
```

- Backend API: `http://localhost:8000` (docs at `/docs`)
- Frontend Dashboard: `http://localhost:8501`

## 📖 Usage

1. **Create a Project** - Open the dashboard and create a new project
2. **Generate Queries** - AI generates search queries based on your goals
3. **Extract Leads** - System automatically extracts company names from search results
4. **Upload Datasets** (Optional) - Merge CSV files with discovered leads
5. **Enrich Leads** - Analyze companies and export enriched data