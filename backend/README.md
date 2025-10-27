# Backend - AI Lead Generator

FastAPI backend for the AI Lead Generator platform.

## Quick Start

### 1. Install Dependencies
```bash
cd backend
```

### 2. Start the Server

**Development server:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Required in `.env` file:
```
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=your_password
POSTGRESQL_DATABASE=ai_lead_generator
POSTGRESQL_INITIAL_DATABASE=postgres
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
SERP_API_KEY=your_serp_key
JINA_API_KEY=your_jina_key
GOOGLE_MAPS_API_KEY=your_google_key
```