"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { BookListItem, getBooks, getPipelineJob, PipelineJob, uploadAndProcess } from "@/lib/api";

export default function BooksPage() {
  const [books, setBooks] = useState<BookListItem[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [job, setJob] = useState<PipelineJob | null>(null);
  const [error, setError] = useState("");

  const loadBooks = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const payload = await getBooks(search, page);
      setBooks(payload.results);
      setCount(payload.count);
    } catch {
      setError("Unable to load books from backend.");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    void loadBooks();
  }, [loadBooks]);

  const handleProcess = async () => {
    try {
      setProcessing(true);
      setError("");
      const result = await uploadAndProcess(10);
      setJob(result.job);
    } catch {
      setError("Book ingestion pipeline failed. Verify backend services and retry.");
      setProcessing(false);
    }
  };

  useEffect(() => {
    if (!job || !processing) return;
    if (job.status === "completed" || job.status === "failed") {
      setProcessing(false);
      void loadBooks();
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        const next = await getPipelineJob(job.id);
        setJob(next);
      } catch {
        setError("Unable to fetch pipeline status.");
        setProcessing(false);
      }
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [job, loadBooks, processing]);

  const totalPages = Math.max(1, Math.ceil(count / 12));

  return (
    <div className="space-y-6">
      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="section-kicker">Book library</p>
            <h1 className="page-title">Book Dashboard</h1>
            <p className="page-lead">
              Internal view of uploaded books, indexed metadata, and review-ready records.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              value={search}
              onChange={(event) => {
                setPage(1);
                setSearch(event.target.value);
              }}
              placeholder="Search title, author, description"
              className="w-full min-w-[12rem] max-w-xs rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 transition-colors placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-400/50"
            />
            <button type="button" onClick={handleProcess} disabled={processing} className="btn-primary shrink-0">
              {processing ? "Processing..." : "Upload & Process"}
            </button>
          </div>
        </div>
      </section>

      {error ? <ErrorState message={error} /> : null}
      {job ? (
        <section className="rounded-md border border-zinc-200 bg-white p-4">
          <div className="flex items-center justify-between gap-2 text-sm">
            <p className="font-medium text-zinc-900">
              <span className="text-zinc-500">Pipeline</span>{" "}
              <span className="capitalize">{job.stage}</span>{" "}
              <span className="font-normal text-zinc-600">({job.status})</span>
            </p>
            <p className="tabular-nums font-medium text-zinc-800">{job.progress_percent}%</p>
          </div>
          <progress
            className="mt-2 h-2 w-full overflow-hidden rounded-full [&::-moz-progress-bar]:bg-zinc-900 [&::-webkit-progress-bar]:bg-zinc-200 [&::-webkit-progress-value]:bg-zinc-900"
            max={100}
            value={job.progress_percent}
          />
          {job.error_message ? <p className="mt-2 text-sm text-red-700">{job.error_message}</p> : null}
        </section>
      ) : null}

      {loading ? (
        <LoadingState variant="grid" label="Loading books..." />
      ) : books.length === 0 ? (
        <EmptyState title="No books available" description="Run upload and processing to populate the dashboard." />
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {books.map((book) => (
            <article key={book.id} className="card-interactive p-5">
              <h2 className="text-lg font-semibold tracking-tight text-zinc-900">{book.title}</h2>
              <p className="mt-1.5 text-sm text-zinc-600">{book.author || "Unknown author"}</p>
              <p className="mt-2.5 text-sm text-zinc-800">
                <span className="text-zinc-500">Rating</span>{" "}
                <span className="font-medium tabular-nums">{book.rating ?? "N/A"}</span>
              </p>
              <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-zinc-600">
                {book.description || "No description available."}
              </p>
              <div className="mt-4 flex items-center justify-between gap-2 border-t border-zinc-100 pt-4">
                <a
                  href={book.book_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-blue-700 underline-offset-4 transition-colors hover:text-blue-900 hover:underline"
                >
                  Source URL
                </a>
                <Link
                  href={`/books/${book.id}`}
                  className="text-sm font-medium text-zinc-900 underline-offset-4 transition-colors hover:underline"
                >
                  View Details
                </Link>
              </div>
            </article>
          ))}
        </section>
      )}

      <section className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-zinc-200 bg-white p-4 text-sm text-zinc-700">
        <p className="tabular-nums">
          Page {page} of {totalPages}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPage((prev) => Math.max(1, prev - 1))}
            disabled={page === 1}
            className="btn-secondary"
          >
            Previous
          </button>
          <button
            type="button"
            onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
            disabled={page >= totalPages}
            className="btn-secondary"
          >
            Next
          </button>
        </div>
      </section>
    </div>
  );
}
