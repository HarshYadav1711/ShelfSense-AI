const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type BookListItem = {
  id: number;
  title: string;
  author: string;
  rating: number | null;
  description: string;
  book_url: string;
  updated_at: string;
};

export type BookDetail = BookListItem & {
  reviews_count: number | null;
  ingestion_status: string;
  last_ingested_at: string | null;
  insights: Array<{ insight_type: string; content: string; updated_at: string }>;
  created_at: string;
};

export type PaginatedBooks = {
  count: number;
  next: string | null;
  previous: string | null;
  results: BookListItem[];
};

export type RagResponse = {
  answer: string;
  sources: Array<{
    book_id: number;
    book_title: string;
    book_url: string;
    chunk_index: number;
    similarity_distance: number | null;
  }>;
  related_books: string[];
  metadata: Record<string, string | number | boolean>;
};

export type PipelineJob = {
  id: number;
  status: string;
  stage: string;
  progress_percent: number;
  limit: number;
  max_pages: number;
  ingestion_run_id: number | null;
  details: Record<string, unknown>;
  error_message: string;
  created_at: string;
  updated_at: string;
};

export type RagHistoryItem = {
  id: number;
  question: string;
  answer: string;
  sources: RagResponse["sources"];
  related_books: string[];
  created_at: string;
};

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export function getBooks(search = "", page = 1): Promise<PaginatedBooks> {
  const query = new URLSearchParams();
  if (search) query.set("search", search);
  query.set("page", String(page));
  query.set("page_size", "12");
  return fetchJson<PaginatedBooks>(`/books/?${query.toString()}`);
}

export function getBookDetail(bookId: number): Promise<BookDetail> {
  return fetchJson<BookDetail>(`/books/${bookId}/`);
}

export function getRelatedBooks(bookId: number): Promise<{ book_id: number; results: BookListItem[] }> {
  return fetchJson<{ book_id: number; results: BookListItem[] }>(`/books/${bookId}/related/`);
}

export function uploadAndProcess(limit = 10): Promise<{
  status: string;
  job: PipelineJob;
}> {
  return fetchJson("/books/upload-process/", {
    method: "POST",
    body: JSON.stringify({ limit, max_pages: 3 }),
  });
}

export function getPipelineJob(jobId: number): Promise<PipelineJob> {
  return fetchJson<PipelineJob>(`/books/upload-process/${jobId}/`);
}

export function askRag(question: string): Promise<RagResponse> {
  return fetchJson<RagResponse>("/rag/ask/", {
    method: "POST",
    body: JSON.stringify({ question, top_k: 4 }),
  });
}

export function getRagHistory(page = 1): Promise<{
  count: number;
  next: string | null;
  previous: string | null;
  results: RagHistoryItem[];
}> {
  return fetchJson(`/rag/history/?page=${page}&page_size=5`);
}
