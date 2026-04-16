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
        <h1 className="text-2xl font-semibold">{book.title}</h1>
        <p className="mt-2 text-sm text-zinc-600">{book.author || "Unknown author"}</p>
        <dl className="mt-4 grid gap-2 text-sm text-zinc-700 md:grid-cols-2">
          <div>
            <dt className="font-medium">Rating</dt>
            <dd>{book.rating ?? "N/A"}</dd>
          </div>
          <div>
            <dt className="font-medium">Reviews</dt>
            <dd>{book.reviews_count ?? "N/A"}</dd>
          </div>
          <div>
            <dt className="font-medium">Ingestion Status</dt>
            <dd>{book.ingestion_status}</dd>
          </div>
          <div>
            <dt className="font-medium">Last Ingested</dt>
            <dd>{book.last_ingested_at ? new Date(book.last_ingested_at).toLocaleString() : "N/A"}</dd>
          </div>
        </dl>
        <p className="mt-4 text-sm text-zinc-700">{book.description || "No description available."}</p>
        <a href={book.book_url} target="_blank" rel="noreferrer" className="mt-4 inline-block text-sm text-blue-700 hover:underline">
          Open Source URL
        </a>
      </section>

      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold">Generated Insights</h2>
        {book.insights.length === 0 ? (
          <EmptyState title="No insights yet" description="Run insight generation to populate this section." />
        ) : (
          <div className="mt-4 grid gap-3">
            {book.insights.map((insight) => (
              <article key={insight.insight_type} className="rounded border border-zinc-200 p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-700">{insight.insight_type}</h3>
                <p className="mt-2 text-sm text-zinc-700">{insight.content}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <h2 className="text-lg font-semibold">Related Books</h2>
        {related.length === 0 ? (
          <EmptyState title="No related books found" description="Related recommendations will appear after more books are indexed." />
        ) : (
          <div className="mt-4 grid gap-3">
            {related.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded border border-zinc-200 p-3">
                <div>
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-xs text-zinc-600">{item.author || "Unknown author"}</p>
                </div>
                <Link href={`/books/${item.id}`} className="text-sm text-zinc-900 hover:underline">
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
