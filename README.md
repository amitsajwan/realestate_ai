# � Real Estate AI CRM Application

A comprehensive Real Estate Customer Relationship Management system with AI-powered features for modern real estate agents.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Optional: MongoDB (for persistent storage)
- Optional: Redis (for session management)

### Installation & Setup

1. **Navigate to the project directory:**
   ```bash
   cd realestate_ai
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Run the application launcher:**
   ```bash
   python run_app.py
   ```

   This will automatically:
   - Install all required dependencies
   - Create a default `.env` file if needed
   - Start the assistant backend (API) on http://localhost:8003 (optional)

### Production CRM (Recommended)

Run the full CRM with MongoDB via Docker:

```bash
docker compose -f docker-compose.crm.yml up -d --build
```

CRM UI: http://localhost:8004

Stop:

```bash
docker compose -f docker-compose.crm.yml down -v
```

### Manual Setup (Alternative)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the assistant backend (optional):**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8003 --reload
   ```

## 🎯 Application URLs

- **CRM UI (Production):** http://localhost:8004
- **Assistant Backend (Optional):** http://localhost:8003
- **API Documentation (assistant backend):** http://localhost:8003/docs
- **Interactive API:** http://localhost:8003/redoc
- **Health Check:** http://localhost:8003/

## � Documentation

- Start here: USER_MANUAL.md — end‑user steps to use the CRM on port 8004
- CODEMAP.md — high‑level map of files and features
- PRODUCTION_READINESS_REPORT.md — status and evidence for production
- DASHBOARD_INTEGRATION_COMPLETE.md — dashboard wiring notes
- HOW_TO_USE_DEMO.md — demo flows and scenarios
- DEMO_RUNBOOK.md — quick demo script
- LAUNCH_CHECKLIST.md — pre‑launch verification
- PRODUCTION_GUIDE.md — deployment guidance
- FEATURE_OVERVIEW.md — feature list and scope
- PROGRESS_OWNER.md — product owner updates and next steps
- SPRINT_PLAN.md — two-week tech-debt sprint plan, roles, and acceptance criteria
- CONTRIBUTING.md — branching, PRs, code style, tests, docs

## 🧪 Tests

- Test layout is organized under `tests/`:
   - `tests/unit/` — fast model/logic tests
   - `tests/integration/` — API/DB/end-to-end tests
   - `tests/helpers/` — shared fixtures/utilities
- Root-level legacy `test_*.py` files remain for backward compatibility and are referenced by wrappers in `tests/`.
- CI runs a smoke check via `tests/smoke_check.py` after starting the CRM on port 8004.

### Modular app (incremental migration)
- App entry: `app/main.py` (templates in `templates/`, static in `static/`)
- Unit tests: `tests/unit/test_modular_app.py`
- To run locally (example):
   - Use uvicorn to run `app.main:app` on another port (e.g., 8005) for side-by-side testing.

## �👤 Demo Credentials

For testing purposes, use these demo credentials:
- **Email:** demo@mumbai.com
- **Password:** demo123
├── images/
│   └── building.png               # Placeholder image to post
└── requirements.txt               # Dependencies
```

---

## ⚒️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/real_estate_assistant.git
cd real_estate_assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your `.env`

```env
FB_PAGE_ID=699986296533656
FB_PAGE_ACCESS_TOKEN=EAAXXXXXXXX... (from me/accounts?access_token=...)
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

### 5. Connect WebSocket

Use a browser frontend or tools like Postman / browser client to connect:

```
ws://localhost:8000/chat
```

Then type `start` to begin the assistant flow.

---

## 🚀 Example Flow

1. Assistant asks branding questions.
2. You reply with branding preferences.
3. Assistant generates:

   * Brand name + tagline
   * Logo and cover image prompts
   * About section
4. You enter property details (location, price, etc.)
5. Assistant generates:

   * Base post + 3 variants
6. You confirm posting to Facebook Page.
7. Assistant posts using image `images/building.png`.

---

## 📸 Facebook Requirements

Ensure your Page has:

* ✅ `pages_manage_posts` & `pages_read_engagement`
* ✅ App has correct permissions and is live
* ✅ You are an admin of the Page

---

## 🧠 Powered by

* [LangGraph](https://github.com/langchain-ai/langgraph)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Groq LLM via LangChain](https://python.langchain.com/docs/integrations/llms/groq)

---

## 📌 TODO

* [ ] Auto-generate and upload logo/cover images
* [ ] Schedule Facebook posts
* [ ] Add Instagram integration
* [ ] Save user projects to database

---

## 🧑‍💻 Author

**Amit Sajwan** — powered by Python, GenAI & LangGraph
