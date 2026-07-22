# Lead Gen AI Agent

An AI-powered lead generation platform that discovers and enriches potential corporate partners through intelligent search and analysis. Built with FastAPI, React + Vite (TypeScript, MUI), and OpenAI.

## 🎬 Demo

View demo here: https://www.youtube.com/watch?v=GLnULm-Nle4

## 🚀 Features

- **AI-Powered Search**: Automatically generates search queries and extracts company names
- **Lead Enrichment**: Analyzes companies for specific attributes (e.g., environmental reports, sustainability)
- **Dataset Management**: Upload and merge CSV/Excel datasets with discovered leads
- **Project Organization**: Organize leads by projects with stats
- **Bring-your-own API keys**: Enter your OpenAI and Jina keys in the UI — no server-side `.env` keys required

## 🔑 API Keys

You supply your **own** OpenAI and Jina API keys directly in the app (the "API Keys" button, top-right). They are:

- stored **only in your browser** (`localStorage`),
- sent with each request that needs them (as `X-OpenAI-Key` / `X-Jina-Key` headers),
- used by the backend to call OpenAI and Jina **on your behalf**.

The backend no longer requires `OPENAI_API_KEY` / `JINA_API_KEY` in its `.env`.

> **Security note:** keys in `localStorage` are readable by any JavaScript running on the page (an XSS risk) and are transmitted to the backend — always serve the app over HTTPS in production. Use the "Clear keys" button to remove them.

## 📋 Prerequisites

**For Local Development:**
- Python 3.9+
- Node.js 18+ and npm (for the frontend)
- PostgreSQL 12+ (installed locally)
- An OpenAI API key and a Jina API key (entered in the UI, not in `.env`)

**For Docker (Alternative):**
- Docker Desktop (or Docker Engine + Docker Compose)
- An OpenAI API key and a Jina API key (entered in the UI, not in `.env`)

## 🛠️ Installation

Choose one of the following approaches:

### Option 1: Local Development (Recommended for Active Coding)

Best for: Faster iteration, easier debugging, active development

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

3. **Set up frontend dependencies (React + Vite):**
```bash
cd ../frontend-react
npm install
# Optional: copy .env.example to .env to point at a non-default backend
# cp .env.example .env   # sets VITE_BACKEND_URL (defaults to http://localhost:8000)
```

4. **Set up backend environment variables:**
```bash
cd ../backend
cp env.example .env
# Edit .env with your database credentials.
# NOTE: OpenAI/Jina API keys are NOT needed here — you enter them in the UI.
# Make sure your PostgreSQL database exists and is configured in .env
```

*Note: The backend will automatically create all required tables when it starts.*

---

### Option 2: Docker Compose (Recommended for Consistency)

Best for: Team collaboration, consistent environments, production-like testing

**Why Docker?**
- ✅ No need to install PostgreSQL locally
- ✅ Consistent environment across all developers
- ✅ Easy onboarding for new team members
- ✅ Matches production environment

**Setup:**

1. **Set up environment variables:**
   ```bash
   # Copy the backend example file
   cp backend/env.example backend/.env
   
   # Edit backend/.env with your database config.
   # You do NOT need to set OPENAI_API_KEY / JINA_API_KEY — those are entered in the UI.
   ```
   
   Docker Compose automatically reads the `.env` file from the `backend/` folder - no shell setup needed!
   
   **Note:** The frontend is a static React build served by nginx. Docker sets `BACKEND_URL=http://localhost:8000` (the browser calls the backend directly on the host).

2. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build Docker images for backend and frontend
   - Start PostgreSQL database container
   - Start backend API (FastAPI)
   - Start frontend UI (Streamlit)

3. **Access the application:**
   - Frontend Dashboard: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

**Useful Docker Commands:**

```bash
# Start in background (detached mode)
docker-compose up -d

# View logs
docker-compose logs -f              # All services
docker-compose logs -f backend      # Specific service
docker-compose logs -f frontend
docker-compose logs -f db

# Stop services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend

# Rebuild after dependency changes
docker-compose build --no-cache backend
docker-compose build --no-cache frontend
```

**Development Mode:**
The backend uses a volume mount, so backend code changes are reflected immediately (you may need to restart it for some changes). The frontend is a static production build served by nginx, so frontend changes require a rebuild:
```bash
docker-compose restart backend            # backend code changes
docker-compose up --build frontend        # rebuild the frontend after changes
```
For fast frontend iteration, prefer the Vite dev server (`cd frontend-react && npm run dev`).

**Troubleshooting:**

- **Backend can't connect to database**
  - Wait a few seconds for the database to be ready
  - Check database logs: `docker-compose logs db`
  - Verify database credentials match in `backend/.env`

- **Frontend can't connect to backend**
  - Check that backend is running: `docker-compose ps`
  - Verify BACKEND_URL environment variable is set correctly
  - Check backend logs: `docker-compose logs backend`

- **Port already in use**
  - Stop any local instances running on ports 8000, 8501, or 5432
  - Or change the port mappings in `docker-compose.yml`

> 📖 **New to Docker?** See [EXPLANATION.md](EXPLANATION.md) for a beginner-friendly explanation of local vs Docker setup

---

## 🚀 Quick Start

### Local Development

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
cd frontend-react
npm run dev
```

**Access:**
- Backend API: `http://localhost:8000` (docs at `/docs`)
- Frontend Dashboard: `http://localhost:5173` (Vite dev server)

Then click **API Keys** (top-right) and enter your OpenAI and Jina keys.

### Docker Development

```bash
# Set environment variables (see Option 2 above)
# Then start everything:
docker-compose up --build
```

**Access:**
- Backend API: `http://localhost:8000` (docs at `/docs`)
- Frontend Dashboard: `http://localhost:8501`

## 📖 Usage

1. **Create a Project** - Open the dashboard and create a new project
2. **Generate Queries** - AI generates search queries based on your goals
3. **Extract Leads** - System automatically extracts company names from search results
4. **Upload Datasets** (Optional) - Merge CSV files with discovered leads
5. **Enrich Leads** - Analyze companies and export enriched data

## 🚢 Production Deployment

For production deployment, consider:

1. **Change default passwords**: Update the PostgreSQL password in `docker-compose.yml`
2. **Use secrets management**: Don't hardcode API keys in docker-compose.yml
3. **Remove volume mounts**: Remove the `volumes` sections for production
4. **Add reverse proxy**: Use nginx or similar for SSL termination
5. **Database backups**: Set up regular backups for the PostgreSQL volume
6. **Resource limits**: Add memory and CPU limits to services
