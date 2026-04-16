"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { BookDetail, BookListItem, getBookDetail, getRelatedBooks } from "@/lib/api";

export default function BookDetailPage() {
  const params = useParams<{ id: string }>();
  const bookId = Number(params.id);

  const [book, setBook] = useState<BookDetail | null>(null);
  const [related, setRelated] = useState<BookListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError("");
        const [detail, relatedPayload] = await Promise.all([getBookDetail(bookId), getRelatedBooks(bookId)]);
        setBook(detail);
        setRelated(relatedPayload.results);
      } catch {
        setError("Unable to load book details.");
      } finally {
        setLoading(false);
      }
    };

    if (!Number.isNaN(bookId)) {
      void load();
    }
  }, [bookId]);

  if (loading) return <LoadingState label="Loading book details..." />;
  if (error) return <ErrorState message={error} />;
  if (!book) return <EmptyState title="Book not found" description="The requested book was not found." />;

  return (
    <div className="space-y-6">
      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <p className="section-kicker">Book detail</p>
        <h1 className="page-title">{book.title}</h1>
        <p className="mt-2 text-sm text-zinc-600">{book.author || "Unknown author"}</p>
        <dl className="mt-5 grid gap-4 text-sm text-zinc-800 md:grid-cols-2">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-zinc-500">Rating</dt>
            <dd className="mt-1 tabular-nums">{book.rating ?? "N/A"}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-zinc-500">Reviews</dt>
            <dd className="mt-1 tabular-nums">{book.reviews_count ?? "N/A"}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-zinc-500">Ingestion status</dt>
            <dd className="mt-1 capitalize">{book.ingestion_status}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-zinc-500">Last ingested</dt>
            <dd className="mt-1">{book.last_ingested_at ? new Date(book.last_ingested_at).toLocaleString() : "N/A"}</dd>
          </div>
        </dl>
        <p className="mt-5 text-sm leading-relaxed text-zinc-700">{book.description || "No description available."}</p>
        <a
          href={book.book_url}
          target="_blank"
          rel="noreferrer"
          className="mt-5 inline-block text-sm text-blue-700 underline-offset-4 transition-colors hover:text-blue-900 hover:underline"
        >
          Open Source URL
        </a>
      </section>

      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <h2 className="section-title">Generated insights</h2>
        {book.insights.length === 0 ? (
          <EmptyState title="No insights yet" description="Run insight generation to populate this section." />
        ) : (
          <div className="mt-4 grid gap-3">
            {book.insights.map((insight) => (
              <article key={insight.insight_type} className="card-interactive rounded-md p-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{insight.insight_type}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-800">{insight.content}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <h2 className="section-title">Related books</h2>
        <p className="mt-1 text-xs text-zinc-500">Ranked by similarity to this book&apos;s description when indexed.</p>
        {related.length === 0 ? (
          <EmptyState title="No related books found" description="Related recommendations will appear after more books are indexed." />
        ) : (
          <div className="mt-4 grid gap-3">
            {related.map((item) => (
              <div
                key={item.id}
                className="card-interactive flex items-center justify-between gap-3 rounded-md p-3"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-zinc-900">{item.title}</p>
                  <p className="text-xs text-zinc-600">{item.author || "Unknown author"}</p>
                </div>
                <Link
                  href={`/books/${item.id}`}
                  className="shrink-0 text-sm font-medium text-zinc-900 underline-offset-4 transition-colors hover:underline"
                >
                  View
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
