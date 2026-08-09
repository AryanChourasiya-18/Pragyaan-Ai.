# Pragyaan — AI Study Buddy

An AI-powered study platform: upload PDF notes/chapters and get summaries, a
chat assistant that answers strictly from the document (with page citations),
auto-generated quizzes (MCQ/short/long/true-false/fill-in-the-blank/HOTS, JEE/NEET
level), Anki-style flashcards with SM-2 spaced repetition, revision notes/formula
sheets/cheat sheets, and an AI-generated day-by-day study planner.

Stack: **React + TypeScript + Tailwind** (frontend), **FastAPI** (backend),
**Postgres** (relational data), **ChromaDB** (vector search / RAG), **OpenAI API**
(LLM + embeddings).

---

## 1. What's implemented vs. what's a roadmap item

This is a working full-stack app, not a mockup — every endpoint below actually
runs. To keep the initial build shippable, some items from the original feature
wishlist are **not** implemented yet and are left as clearly-scoped extension
points:

| Implemented | Not yet implemented (roadmap) |
|---|---|
| PDF upload + OCR fallback for scanned PDFs | Native mobile apps (Android/iOS) |
| AI summary (6 styles) | Teacher mode (multi-user assignments, class reports) |
| AI chat with RAG + page citations | Voice mode (speech-to-text/text-to-speech) |
| Question generator (6 types, JEE/NEET, difficulty) | Built-in dictionary widget |
| Quiz mode (timer, negative marking, scoring, explanations) | YouTube lecture recommendations |
| Flashcards with SM-2 spaced repetition | Interactive knowledge graph |
| Notes generator (5 kinds) | Multi-language UI (English only for now) |
| AI study planner | Mistake notebook (schema exists, no dedicated UI yet) |
| Performance analytics (weak/strong subjects) | Social login (Clerk/Firebase) — JWT auth is the default; see below |
| JWT auth (register/login) | Cloud sync across devices beyond the DB itself (works, but no offline-first sync) |

Each roadmap item has a natural home in the existing structure (e.g. Teacher
Mode is a `role="teacher"` check plus a new router; Voice Mode is a browser
`SpeechRecognition`/`SpeechSynthesis` wrapper around the existing chat endpoint).

---

## 2. Local development

### Prerequisites
- Docker + Docker Compose (easiest path), **or** Python 3.11+ and Node 18+ installed locally
- An OpenAI API key (for LLM + embeddings) — swap `app/services/ai_service.py` and
  `vector_service.py` if you'd rather use Anthropic or another provider
- `poppler-utils` and `tesseract-ocr` installed if running the backend outside Docker (needed for OCR)

### Option A — Docker (recommended)
```bash
cp backend/.env.example backend/.env
# edit backend/.env and set OPENAI_API_KEY

docker compose up --build
```
This starts Postgres on `5432` and the API on `http://localhost:8000`.

Then, in a separate terminal, run the frontend (Vite has no Docker setup here
since hot-reload is nicer run natively):
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Visit `http://localhost:5173`.

### Option B — fully native
```bash
# Postgres: point DATABASE_URL in backend/.env at any Postgres instance you have running

cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit values
uvicorn app.main:app --reload

# in another terminal
cd frontend
npm install
cp .env.example .env
npm run dev
```

API docs (Swagger UI) are auto-generated at `http://localhost:8000/docs`.

---

## 3. Deployment

### Backend → Render (or Railway)
`backend/render.yaml` is a ready-to-use Render Blueprint:
1. Push this repo to GitHub.
2. In Render, "New +" → "Blueprint" → point at the repo.
3. Render provisions a Postgres instance and the API service from `Dockerfile` automatically.
4. Set `OPENAI_API_KEY` and `FRONTEND_ORIGIN` (your deployed frontend URL) in the Render dashboard — they're marked `sync: false` in the blueprint so they aren't committed to git.

Railway works the same way: create a Postgres plugin, deploy `backend/` as a
Dockerfile service, and set the same env vars.

### Frontend → Vercel
1. Import the repo in Vercel, set the project root to `frontend/`.
2. Framework preset: Vite.
3. Set env var `VITE_API_BASE_URL` to your deployed backend URL (e.g. `https://pragyaan-api.onrender.com`).
4. Deploy.

### Storage (PDFs)
Defaults to local disk (fine for a single Render instance with a persistent
disk attached). For multi-instance or serverless deployments, set
`STORAGE_BACKEND=s3` in the backend env and fill in the `S3_*` vars — this
works directly with Supabase Storage (S3-compatible) or AWS S3.

### Auth: swapping JWT for Clerk/Firebase
The app ships with a simple, fully working JWT auth system
(`app/security.py`, `app/routers/auth.py`) so it runs standalone without any
third-party account. To use Clerk or Firebase Auth instead (for Google/Apple/
GitHub login):
1. Replace `get_current_user` in `app/security.py` with one that verifies the
   Clerk/Firebase session token instead of your own JWT.
2. Remove `/auth/register` and `/auth/login` (Clerk/Firebase handle this
   client-side) and swap the frontend's `lib/auth.tsx` for the relevant SDK's
   React hooks.
   All other routers are unaffected since they only depend on `get_current_user`.

---

## 4. Project structure

```
pragyaan/
  backend/
    app/
      main.py            # FastAPI app + router registration
      config.py           # env-driven settings
      database.py          # SQLAlchemy session
      models.py            # ORM models (users, documents, quizzes, flashcards, ...)
      schemas.py            # Pydantic request/response models
      security.py            # JWT auth
      services/
        pdf_service.py        # text extraction + OCR fallback
        vector_service.py      # ChromaDB indexing/retrieval (RAG)
        ai_service.py            # all LLM calls (summary/chat/quiz/flashcards/notes)
        storage_service.py        # local disk or S3 file storage
      routers/
        auth.py, documents.py, ai.py, quiz.py, flashcards.py, notes.py, planner.py, analytics.py
    Dockerfile
    render.yaml
    requirements.txt
    .env.example
  frontend/
    src/
      lib/          # api client, auth context
      components/    # Layout, Sidebar
      pages/          # Login, Dashboard, Upload, Chat, Quiz, Flashcards, Notes, Planner
    tailwind.config.js
    package.json
  docker-compose.yml    # local Postgres + API
  README.md
```

---

## 5. Swapping the AI provider

All LLM calls live in `backend/app/services/ai_service.py` and
`vector_service.py`, both built against the OpenAI SDK. To use Claude or
another provider instead: replace the `OpenAI(...)` client and `_chat()` /
`_embedder` calls in those two files — every router calls into these two
files only, so no other code needs to change.
