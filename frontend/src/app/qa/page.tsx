"use client";

import { FormEvent, useState } from "react";
import { useEffect } from "react";

import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { askRag, getRagHistory, RagHistoryItem, RagResponse } from "@/lib/api";

export default function QaPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<RagResponse | null>(null);
  const [history, setHistory] = useState<RagHistoryItem[]>([]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!question.trim()) return;

    try {
      setLoading(true);
      setError("");
      const payload = await askRag(question.trim());
      setResult(payload);
    } catch {
      setError("Unable to fetch answer from RAG service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const payload = await getRagHistory(1);
        setHistory(payload.results);
      } catch {
        // Keep page usable even when history endpoint is unavailable.
      }
    };
    void loadHistory();
  }, [result]);

  return (
    <div className="space-y-6">
      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <p className="section-kicker">Retrieval Q&A</p>
        <h1 className="page-title">Book Q&A</h1>
        <p className="page-lead">
          Ask grounded questions against indexed book content. Answers include visible source citations.
        </p>
        <form onSubmit={handleSubmit} className="mt-5 flex flex-col gap-3">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
            placeholder="Example: Which books have strong positive recommendations and why?"
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 transition-colors placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-400/50"
          />
          <button type="submit" disabled={loading} className="btn-primary w-fit">
            {loading ? "Thinking..." : "Ask"}
          </button>
        </form>
      </section>

      {error ? <ErrorState message={error} /> : null}

      {!result ? (
        <EmptyState title="No answer yet" description="Submit a question to run retrieval and grounded generation." />
      ) : (
        <section className="space-y-4">
          <article className="rounded-md border border-zinc-200 bg-white p-6">
            <h2 className="section-title">Answer</h2>
            <p className="mt-3 text-sm leading-relaxed text-zinc-700">{result.answer}</p>
          </article>

          <article className="rounded-md border border-zinc-200 bg-white p-6">
            <h2 className="section-title">Sources</h2>
            {result.sources.length === 0 ? (
              <p className="mt-3 text-sm text-zinc-600">No sources were retrieved.</p>
            ) : (
              <div className="mt-4 grid gap-3">
                {result.sources.map((source, index) => (
                  <div
                    key={`${source.book_id}-${source.chunk_index}-${index}`}
                    className="card-interactive rounded-md p-3 text-sm"
                  >
                    <p className="font-medium text-zinc-900">
                      [{index + 1}] {source.book_title}
                    </p>
                    <p className="mt-1 text-zinc-600">Chunk: {source.chunk_index}</p>
                    <p className="text-zinc-600">Distance: {source.similarity_distance ?? "N/A"}</p>
                    <a
                      href={source.book_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-blue-700 underline-offset-4 transition-colors hover:text-blue-900 hover:underline"
                    >
                      Open source
                    </a>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>
      )}

      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <h2 className="section-title">Recent Q&A history</h2>
        <p className="mt-1 text-xs text-zinc-500">Previously answered questions from the API.</p>
        {history.length === 0 ? (
          <p className="mt-4 text-sm text-zinc-600">No recent Q&A history yet.</p>
        ) : (
          <div className="mt-4 grid gap-3">
            {history.map((item) => (
              <article key={item.id} className="card-interactive rounded-md p-3 text-sm">
                <p className="font-medium text-zinc-900">{item.question}</p>
                <p className="mt-1.5 leading-relaxed text-zinc-600">{item.answer}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
