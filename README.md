# Lead Gen AI Agent

An AI-powered lead generation platform that discovers and enriches potential corporate partners through intelligent search and analysis. Built with FastAPI, Streamlit, and OpenAI.

## 🎬 Demo

[Watch the Demo]()

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

1. **Clone the repository:**
```bash
git clone <repository-url>
cd lead-gen-ai-agent
```

2. **Set up backend virtual environment and dependencies:**
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

3. **Set up frontend virtual environment and dependencies:**
```bash
cd ../frontend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

4. **Set up backend environment variables:**
```bash
cd ../backend
cp env.example .env
# Edit .env with your API keys and database credentials
# Make sure your PostgreSQL database exists and is configured in .env
```

*Note: The backend will automatically create all required tables when it starts.*

## 🚀 Quick Start

**Start the backend:**
```bash
cd backend
# Activate backend virtual environment first
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

python -m uvicorn app.main:app --reload --port 8000
```

**Start the frontend:**
```bash
cd frontend
# Activate frontend virtual environment first
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

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