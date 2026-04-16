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
* Modular and scalable architecture

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
| AI Models  | Sentence Transformers + LLM (LM Studio / OpenAI) |
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

✔ Ensures accurate, context-aware answers
✔ Reduces hallucination
✔ Provides explainability via citations

---

### 4. REST API Endpoints

#### GET APIs

```
GET /api/books/                      → List all books
GET /api/books/<id>/                → Book details
GET /api/books/<id>/recommendations/ → Related books
```

#### POST APIs

```
POST /api/books/upload/ → Scrape & process books
POST /api/ask/          → Ask questions (RAG)
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

### 2b) Pipeline worker (async jobs without Redis/Celery)

`POST /api/v1/books/upload-process/` enqueues a `PipelineJob` with `status=pending`. A separate worker process claims jobs from the database and runs the pipeline.

Open a second terminal:

```bash
cd backend
.venv\Scripts\Activate.ps1
python manage.py run_worker
```

Optional tuning:

```bash
python manage.py run_worker --poll-interval 1
```

Failed jobs can be retried by the worker on the next poll cycle (`pending` and `failed` are eligible).

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

## Sample Questions

Try asking:

* "Summarize this book"
* "What genre is this book?"
* "Recommend similar books"
* "What is this book about?"

---

## Sample Output

```json
{
  "answer": "This book explores...",
  "sources": ["Book Title A", "Book Title B"]
}
```

---

## Design Decisions

* **Django REST** chosen for rapid API development and scalability
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
* Efficient to run
* Practical to scale

---