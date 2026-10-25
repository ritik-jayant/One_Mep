# Fire Design Agent

Engineer-in-the-loop agent that turns a plot diagram into an NBC-aware fire-fighting layout, evaluates it against past mistakes and approved plans, then exports editable CAD (DXF). The agent learns from every denial, eval failure, and engineer edit.

## Flow (matches the project chart)

1. Client shares a plot diagram.
2. Engineer uploads it; the drawing is saved.
3. Agent matches **NBC skills** (LLM + rules DB).
4. Engineer confirms or denies the rule set (denied → re-check).
5. Agent reads the **design store** (past issues) so it does not repeat them.
6. Agent generates a design.
7. Agent evaluates against **approved plans**. Failures are stored and generation retries.
8. Agent writes an editable **DXF**.
9. Engineer validates. Minor change → design store. Major change → regenerate.
10. Final design goes to the client and is saved into the approved-plan library.

Legend: purple steps need an LLM, teal steps need the database, orange boxes are retry loops.

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, SQLite (swap to Postgres via `DATABASE_URL`) |
| Agent / LLM | OpenAI-compatible API, default `gpt-4o` (vision + structured JSON). Works with OpenAI, Azure, Groq, OpenRouter |
| CAD | `ezdxf` → `.dxf` |
| Frontend | React + Vite + TypeScript |

If `LLM_API_KEY` is missing, the pipeline still runs on a deterministic NBC fallback so you can demo the loop locally.

## Layout

```
backend/app/          FastAPI app, models, agent pipeline
backend/app/knowledge  Seeded NBC fire-fighting skills
frontend/             Engineer UI (upload → confirm → generate → validate)
data/                 Uploads, DXF output, SQLite file
```

## Run

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
python -m app.main
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.
