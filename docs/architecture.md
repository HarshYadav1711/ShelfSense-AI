# ShelfSense AI Architecture

## Service Boundaries

- **Frontend (`frontend/`)**: Next.js product UI for dashboard, book detail, and Q&A.
- **API (`backend/`)**: Django REST Framework with versioned routes under `/api/v1`.
- **Scraper (`scraper/`)**: Selenium client for bounded, repeatable public-source extraction.

## Data Layer

- **MySQL** stores normalized operational entities:
  - `Book`
  - `BookChunk`
  - `BookInsight`
  - `IngestionRun`, `IngestionLog`, `PipelineJob`
  - `RagQueryCache`, `RagChatHistory`
- **ChromaDB** stores dense vectors for `BookChunk` records and supports top-k retrieval.

## Pipeline Flow

1. **Ingestion trigger** (`POST /api/v1/books/upload-process/`) launches a background `PipelineJob`.
2. **Selenium scrape** reads a bounded number of pages (`max_pages`) from `books.toscrape.com`.
3. **Normalization + persistence** writes/updates books idempotently (`source_site + source_id`).
4. **Chunking** splits descriptions into overlapping windows (80 words, 20-word overlap).
5. **Insights generation** creates summary, genre, recommendation, and sentiment entries.
6. **Vector indexing** embeds chunks with Sentence Transformers and upserts into Chroma.
7. **RAG Q&A** retrieves relevant chunks and produces grounded local-model answers with citations.

## Reliability Controls

- Idempotent upserts for books, chunks, insights, and vectors
- Cache-aware insight generation and RAG responses
- Retry-safe ingestion logging and stage-based job progress
- User-safe error payloads (no internal stack traces in API responses)
