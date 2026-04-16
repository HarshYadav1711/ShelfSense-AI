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
        <h1 className="text-2xl font-semibold">Book Q&A</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Ask grounded questions against indexed book content. Answers include visible source citations.
        </p>
        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
            placeholder="Example: Which books have strong positive recommendations and why?"
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-fit rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60"
          >
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
            <h2 className="text-lg font-semibold">Answer</h2>
            <p className="mt-2 text-sm text-zinc-700">{result.answer}</p>
          </article>

          <article className="rounded-md border border-zinc-200 bg-white p-6">
            <h2 className="text-lg font-semibold">Sources</h2>
            {result.sources.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-600">No sources were retrieved.</p>
            ) : (
              <div className="mt-3 grid gap-3">
                {result.sources.map((source, index) => (
                  <div key={`${source.book_id}-${source.chunk_index}-${index}`} className="rounded border border-zinc-200 p-3 text-sm">
                    <p className="font-medium">
                      [{index + 1}] {source.book_title}
                    </p>
                    <p className="text-zinc-600">Chunk: {source.chunk_index}</p>
                    <p className="text-zinc-600">Distance: {source.similarity_distance ?? "N/A"}</p>
                    <a href={source.book_url} target="_blank" rel="noreferrer" className="text-blue-700 hover:underline">
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
        <h2 className="text-lg font-semibold">Recent Q&A History</h2>
        {history.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-600">No recent Q&A history yet.</p>
        ) : (
          <div className="mt-3 grid gap-3">
            {history.map((item) => (
              <article key={item.id} className="rounded border border-zinc-200 p-3 text-sm">
                <p className="font-medium text-zinc-800">{item.question}</p>
                <p className="mt-1 text-zinc-600">{item.answer}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
