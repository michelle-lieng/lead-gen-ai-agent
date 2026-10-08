# Lead Gen AI Agent

An AI-powered lead generation platform that discovers and enriches potential corporate partners through intelligent search and analysis. Built with FastAPI, React + Vite (TypeScript), and OpenAI.

The interface is a **register**: a projects page listing your registers, and a project page holding one ruled table of companies beside an enquiry desk. You type one sentence — the kind of companies you want, or one question you want answered about every company — and the agent does the rest.

## 🎬 Demo

View demo here: https://www.youtube.com/watch?v=GLnULm-Nle4

## 🚀 Features

- **One sentence in, leads out**: describe the companies you want; the agent writes the search queries, runs them, reads every source, and rules the companies it finds into the register.
- **One sentence in, a column out**: ask a question about every entry ("does this clinic have more than one doctor?"); the agent drafts the full enrichment configuration — column name, goal, evidence standard, result format — researches each company, and writes the answers in.
- **A table you can correct**: cells are edited in place and entries can be struck from the register.
- **Visible working**: each answer keeps the agent's reasoning and the source it came from, readable per entry.
- **Honest progress**: long runs report real step boundaries, real counts, and real elapsed time. Enrichment is sent in small batches so the progress shown is the progress made.
- **Dataset import**: merge a CSV or Excel list into the same register, matched on company name.
- **One shared password**: the whole app opens only with the password set on the server.

## 🔑 Keys and password

Everything secret lives in the backend's environment (`backend/.env` locally, env vars on Render):

| Variable | Purpose |
|----------|---------|
| `APP_PASSWORD` | The shared password that opens the app. |
| `AUTH_SECRET` | Signs sessions. Changing it, or the password, signs everyone out. |
| `OPENAI_API_KEY` | Needed for searches and columns. |
| `JINA_API_KEY` | Needed for searches and columns (raw key, no `jina_` prefix). |
| `GOOGLE_PLACES_API_KEY` | Optional: location searches also search Google Maps. |

Opening the app asks for the password. A session lasts until the browser tab closes (at most 12 hours), and **Sign out** in the sidebar ends it early. Every `/api` route except `/api/health` and the login answers 401 without a session, and 503 if the server has no password set. Nobody enters API keys in the browser.

## 📋 Prerequisites

**For Local Development:**
- Python 3.9+
- Node.js 18+ and npm (for the frontend)
- PostgreSQL 12+ (installed locally)
- An OpenAI API key and a Jina API key (set in `backend/.env`)

**For Docker (Alternative):**
- Docker Desktop (or Docker Engine + Docker Compose)
- An OpenAI API key and a Jina API key (set in `backend/.env`)

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
# Edit .env with your database credentials, APP_PASSWORD, AUTH_SECRET and
# your OpenAI and Jina keys (GOOGLE_PLACES_API_KEY is optional).
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
   - Start frontend UI (static React build served by nginx)

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

Then enter the password you set as `APP_PASSWORD`.

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

1. **Enter your keys** — click the key status in the top right and paste your OpenAI and Jina keys. Nothing runs without them.
2. **Open a register** — "New register" on the projects page. One register holds one search and every column you ask about it.
3. **Find leads** — in the Find leads tab, describe the companies you want in a sentence ("Dental clinics in Sydney"). The agent expands that into search queries, runs them, reads the sources, and adds every company it finds. This takes a few minutes; the panel reports each step as it completes.
4. **Add a column** — switch to the Enrich leads tab and ask one question about every entry. The agent defines the column and researches each company in batches, filling the table as it goes.
5. **Correct and export** — double-click any cell to fix it, strike bad entries, and export the whole register as CSV. Click an entry's chevron to read the agent's reasoning and the source it used.

**Import instead**: the Import button above the table merges a CSV or Excel list into the register, matched on company name.

## 🚢 Production Deployment

For production deployment, consider:

1. **Change default passwords**: Update the PostgreSQL password in `docker-compose.yml`
2. **Use secrets management**: Don't hardcode API keys in docker-compose.yml
3. **Remove volume mounts**: Remove the `volumes` sections for production
4. **Add reverse proxy**: Use nginx or similar for SSL termination
5. **Database backups**: Set up regular backups for the PostgreSQL volume
6. **Resource limits**: Add memory and CPU limits to services
