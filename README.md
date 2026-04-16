# ShelfSense AI

ShelfSense AI is a full-stack book intelligence tool built for the internship assessment. It ingests public book metadata with Selenium, stores normalized records in MySQL, generates AI insights locally, and answers grounded questions through a RAG pipeline.

The implementation is intentionally product-oriented: clear module boundaries, versioned API routes, deterministic AI flows, and UI states that support internal review workflows.

## Free and Local-Only Tooling

This project uses only free, locally runnable components:
- Django REST Framework + Next.js + Tailwind
- MySQL for metadata
- ChromaDB for local vector search
- Sentence Transformers for embeddings
- Ollama or LM Studio for local generation
- Selenium against a public source (`books.toscrape.com`)

No paid APIs, no billing dependencies, and no API keys are required.

## Why This Stack

- **Django REST Framework:** fast delivery of stable, versioned JSON APIs with clean serializers and validation.
- **Next.js + Tailwind:** rapid internal-product UI development with strong TypeScript ergonomics.
- **MySQL + ChromaDB:** separates transactional metadata from semantic retrieval concerns.
- **Sentence Transformers + Local LLM:** practical RAG quality with predictable local execution costs.
- **Selenium:** reliable assignment-compliant automation for repeatable ingestion.

## Architecture

See `docs/architecture.md` for a concise architecture view. High-level flow:
1. Selenium scraper fetches a bounded multi-page batch.
2. Ingestion normalizes metadata and writes `Book`, `BookChunk`, and logs.
3. Insights layer writes summary/genre/recommendation/sentiment.
4. RAG layer embeds chunks into Chroma and serves grounded Q&A with citations.
5. Frontend exposes dashboard, detail, and Q&A views.

## Repository Layout

- `backend/` Django API, ingestion, insights, and RAG services
- `frontend/` Next.js client app
- `scraper/` Selenium source client
- `samples/` sample input/output, request/response payloads
- `docs/` architecture and screenshot assets
- `requirements.txt` Python dependencies

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

### Optional local sample data

```bash
cd backend
python manage.py generate_sample_books
```

## API Documentation

- OpenAPI schema: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`

Core endpoints:
- `GET /api/v1/books/`
- `GET /api/v1/books/{id}/`
- `GET /api/v1/books/{id}/related/`
- `POST /api/v1/books/upload-process/`
- `GET /api/v1/books/upload-process/{jobId}/`
- `POST /api/v1/rag/ask/`
- `GET /api/v1/rag/history/`

Sample requests and responses are included in `samples/api/`.

## Sample Questions and Answers

Example questions (grounded against indexed book chunks):
- "Which books are strongly recommended and why?"
- "What themes appear in books with high ratings?"
- "Show books related to metadata pipelines."

Representative answer and citations are included in:
- `samples/api/responses/rag_ask_success.json`

## UI Screenshots (Submission)

Add 3 to 4 screenshots in `docs/screenshots/` and keep filenames:
- `dashboard-books.png`
- `book-detail.png`
- `qa-with-citations.png`
- `pipeline-progress.png`

Then reference them here:
![Dashboard](docs/screenshots/dashboard-books.png)
![Book Detail](docs/screenshots/book-detail.png)
![Q&A with Citations](docs/screenshots/qa-with-citations.png)
![Pipeline Progress](docs/screenshots/pipeline-progress.png)

## Bonus Features Implemented

- RAG response cache keyed by question + retrieval parameters + index stamp
- Persisted Q&A chat history endpoint
- Async background pipeline job with progress stages
- Multi-page scraping with bounded `max_pages`
- Overlap chunking (`80` words, `20` overlap)
- Retry-safe ingestion and user-safe API error payloads
