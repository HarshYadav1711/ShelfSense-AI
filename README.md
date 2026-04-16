# ShelfSense AI

### Intelligent Book Insights & Question-Answering Platform

ShelfSense AI is a full-stack **Document Intelligence Platform** that transforms raw book data into meaningful insights using **AI and Retrieval-Augmented Generation (RAG)**.

Built as part of the Ergosphere Solutions Internship Assignment, this project demonstrates **end-to-end system design**, combining **data ingestion, backend engineering, AI pipelines, and user-facing interfaces** into a cohesive product.

---

## Key Features

* Automated book data collection using Selenium
* AI-generated insights (summary, genre, recommendations)
* RAG-based question answering over book content
* Fast semantic search using vector embeddings
* RESTful APIs built with Django REST Framework
* Clean and responsive UI with Next.js + Tailwind CSS
* Modular architecture designed for scalability

---

## System Architecture

```
[Selenium Scraper] → [Django Backend] → [MySQL]
                              ↓
                     [Chunking + Embeddings]
                              ↓
                        [ChromaDB]
                              ↓
                       [RAG Pipeline]
                              ↓
                        [REST APIs]
                              ↓
                 [Next.js Frontend]
```

---

## Tech Stack

| Layer      | Technology                                       |
| ---------- | ------------------------------------------------ |
| Backend    | Django REST Framework                            |
| Frontend   | Next.js, Tailwind CSS                            |
| Database   | MySQL                                            |
| Vector DB  | ChromaDB                                         |
| AI Models  | Sentence Transformers + local LLM (Ollama or LM Studio via `LOCAL_LLM_PROVIDER`) |
| Automation | Selenium                                         |

---

## Core Functionality

### 1. Data Ingestion

* Scrapes book data from web sources using Selenium
* Extracts:

  * Title
  * Author
  * Rating
  * Description
  * Book URL
* Stores structured metadata in MySQL

---

### 2. AI Insight Generation

For each book, the system generates:

* **Summary** → concise 2–3 line overview
* **Genre Classification** → predicted category
* **Recommendations** → “If you like X, you’ll like Y”

These insights are generated using LLM prompts and stored for fast retrieval.

---

### 3. RAG Pipeline (Core Highlight)

The system implements a complete **Retrieval-Augmented Generation pipeline**:

1. Book descriptions are split into chunks
2. Chunks are converted into embeddings
3. Stored in ChromaDB (vector database)
4. User query is embedded
5. Top-k similar chunks retrieved
6. Context constructed
7. LLM generates answer with **source references**

✔ Context-grounded answers with explicit source passages
✔ Retrieval step constrains the model to indexed text
✔ Explainability via per-chunk citations

---

### 4. REST API Endpoints

Base path: **`/api/v1/`**.

#### GET

```
GET  /api/v1/books/                              → List books (pagination & filters)
GET  /api/v1/books/<id>/                         → Book details
GET  /api/v1/books/<id>/related/                 → Related books
GET  /api/v1/books/upload-process/<job_id>/      → Pipeline job status
GET  /api/v1/rag/status/                         → RAG module health
GET  /api/v1/rag/history/                        → Past Q&A (paginated)
```

#### POST

```
POST /api/v1/books/upload-process/  → Enqueue scrape + insights + indexing (requires worker)
POST /api/v1/rag/ask/               → Ask a question (RAG)
POST /api/v1/rag/index/             → Run vector indexing (optional; worker also indexes)
```

---

## Frontend Overview

### Dashboard

* Displays all books in a clean card layout
* Shows title, author, rating, description

### Book Detail Page

* Full book metadata
* AI-generated insights

### Q&A Interface

* Ask questions about books
* Displays answers with **source citations**

---

## Optimization & Bonus Features

* ✅ Response caching (avoids repeated AI calls)
* ✅ Overlapping chunk strategy for better context
* ✅ Loading states for improved UX
* ✅ Clean modular backend architecture
* ✅ Error handling in scraping pipeline

---

## 📸 Screenshots

> (Add 3–4 screenshots here)

* Dashboard View
* Book Detail Page
* Q&A Interface
* API Response Example

---

## Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/your-username/shelfsense-ai.git
cd shelfsense-ai
```

### 2. Backend Setup

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

By default, `backend/.env.example` runs on **SQLite** so `migrate` works immediately after copying `.env`.

To run the full assignment stack on **MySQL**, set in `backend/.env`:

```env
USE_MYSQL=1
MYSQL_PASSWORD=...real password...
```

If `migrate` fails with `cryptography package is required for caching_sha2_password`, install dependencies again from the repo root `requirements.txt` (it includes `cryptography` for MySQL 8 default auth with PyMySQL), or switch the MySQL user plugin to `mysql_native_password`.

### 2b) Background pipeline jobs

`POST /api/v1/books/upload-process/` writes a `PipelineJob` row (`pending`). A **separate process** must run the worker so ingestion, insights, and indexing complete. See [How to run the worker](#how-to-run-the-worker).

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Run Scraper

```bash
cd scraper
python scraper.py
```

---

## How to run the worker

The backend uses a **database-backed worker** (no Redis/Celery in this repository): one process polls `PipelineJob` rows, claims a job with row-level locking, and runs **ingestion → insights → vector indexing** to completion.

**When to start it:** Before or after calling `POST /api/v1/books/upload-process/`. Without the worker, jobs remain `pending` and no books are scraped or indexed.

**Steps** (from the repo root, with the same virtualenv and `requirements.txt` as the API):

```bash
cd backend
# Windows PowerShell
.venv\Scripts\Activate.ps1
python manage.py run_worker
```

```bash
cd backend
# Linux / macOS
source .venv/bin/activate
python manage.py run_worker
```

**Options:**

```bash
python manage.py run_worker --poll-interval 1
```

`--poll-interval` (default **2** seconds) controls how long the worker sleeps when no eligible job is available. Eligible statuses include `pending` and `failed` (failed jobs can be picked up again on a later poll).

**Concurrency model:** The design assumes **one worker process** per environment. Multiple workers are not coordinated beyond database locking; for this assignment scope, run a single worker for predictable behavior.

---

## Sample Questions

Try asking:

* "Summarize this book"
* "What genre is this book?"
* "Recommend similar books"
* "What is this book about?"

---

## Sample Output

Shape of `POST /api/v1/rag/ask/` (abbreviated):

```json
{
  "answer": "This book explores...",
  "sources": [
    {
      "book_id": 1,
      "book_title": "Example Title",
      "book_url": "https://books.toscrape.com/...",
      "chunk_index": 0,
      "similarity_distance": 0.42
    }
  ],
  "related_books": ["Example Title"],
  "metadata": {
    "top_k": 4,
    "retrieved_chunks": 1,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "collection": "shelfsense-book-chunks",
    "cache_hit": false
  }
}
```

---

## Design Decisions

* **Django REST** chosen for rapid API development and a structure **designed for scalability** (clear service boundaries, batch-friendly indexing)
* **ChromaDB** used for lightweight vector search
* **Sentence Transformers** for efficient embeddings
* **Next.js** for fast and responsive UI
* **RAG architecture** to ensure factual and explainable answers

---

## Trade-offs

* Used lightweight models for faster inference over heavy models
* Focused on clarity and modularity instead of over-engineering
* Prioritized working RAG pipeline over complex UI features

---

## Reliability considerations

* **Pipeline heartbeats:** `PipelineJob` rows track **`last_heartbeat_at`** while a job is `processing`. The worker refreshes this on claim, on pipeline progress updates, and on a short interval during long steps. On startup, **`run_worker`** reclaims **stale** jobs (no recent heartbeat) by marking them **`failed`** with a clear error message so they are never left stuck in `processing` after a crash. Tune **`PIPELINE_STALE_HEARTBEAT_SECONDS`** and **`PIPELINE_HEARTBEAT_INTERVAL_SECONDS`** as needed.
* **Idempotent ingestion:** Books are upserted by **`(source_site, source_id)`**; chunk content is replaced per run with stable hashing in metadata. Re-running ingestion or retrying after a failed pipeline does not create duplicate book rows for the same catalog entry.
* **RAG response cache:** `POST /api/v1/rag/ask/` stores answers in **`RagQueryCache`** keyed by question, `top_k`, and an index stamp derived from chunk activity, so repeated questions avoid redundant embedding and LLM work when the index has not changed.

---

## System limitations

These boundaries are intentional for the assignment scope and keep expectations aligned with what the repository ships.

* **LLM dependency:** Insight generation and RAG answers call a **local or remote LLM** (for example via LM Studio or Ollama) using settings in `backend/.env`. If that endpoint is down or misconfigured, answers may fall back to safe defaults while the rest of the API stays up.
* **Single-worker pipeline:** Background work uses **`python manage.py run_worker`** polling the database—not a distributed queue. Throughput is **one job at a time** per worker process; horizontal scaling would require additional infrastructure beyond this codebase.
* **Demo data source:** Ingestion is built around **[books.toscrape.com](https://books.toscrape.com/)**—a small, static catalog useful for demos and tests, not a stand-in for a large commercial book dataset.

---

## Project Structure

```
ShelfSense-AI/
├── backend/
├── frontend/
├── scraper/
├── vector_store/
├── samples/
├── README.md
├── requirements.txt
```

---

## What This Project Demonstrates

* End-to-end full-stack development
* Practical AI integration (not just theory)
* Real-world RAG implementation
* Clean system design & modular code
* Problem-solving with performance considerations

---

## Final Note

This project was built with a focus on **clarity, functionality, and real-world applicability** rather than unnecessary complexity.

The goal was to design a system that is:

* Easy to understand
* Efficient to run on a developer machine
* Straightforward to extend with additional data sources, workers, or deployment tooling as requirements grow

---