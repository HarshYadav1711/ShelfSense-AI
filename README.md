# ShelfSense AI Monorepo Scaffold

Production-minded scaffold for a full-stack internship assessment using free, local-first tools.

## Stack

- Backend: Django + Django REST Framework
- Frontend: Next.js (TypeScript) + Tailwind CSS
- Metadata database: MySQL
- Vector database: ChromaDB (local)
- Scraping: Selenium
- Local LLM runtime: Ollama or LM Studio

## Repository Layout

- `backend/` Django API service
- `frontend/` Next.js web app
- `scraper/` Selenium ingestion jobs
- `samples/` sample raw and processed data
- `docs/` architecture and operational notes
- `requirements.txt` Python dependencies for backend and data pipeline tooling

## Quick Start

## 1) Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Backend URLs:
- Health check: `http://localhost:8000/health/`
- API root prefix: `http://localhost:8000/api/v1/`
- API schema: `http://localhost:8000/api/schema/`
- API docs: `http://localhost:8000/api/docs/`

## 2) Frontend

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`.

## API Scaffold Endpoints

- `GET /api/v1/books/status/`
- `GET /api/v1/ingestion/status/`
- `GET /api/v1/insights/status/`
- `GET /api/v1/rag/status/`

These status endpoints keep the scaffold clean while preparing module boundaries for feature development.

## AI Layer Endpoints

- `POST /api/v1/insights/generate/` with `{ "limit": 10 }`
- `POST /api/v1/rag/index/` with `{ "limit": 200 }`
- `POST /api/v1/rag/ask/` with `{ "question": "...", "top_k": 4 }`

## Chunking Strategy

Book descriptions are chunked with overlapping windows:

- chunk size: `80` words
- overlap: `20` words

This keeps local context continuity for retrieval while staying simple to explain during review.

## Local-Only AI Setup

- Embeddings: Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`)
- Vector DB: Chroma (`backend/.chroma`)
- Generation: local Ollama or LM Studio (configured through `backend/.env`)
