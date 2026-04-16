import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";

export default function Home() {
  return (
    <div className="space-y-6">
      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <h1 className="text-2xl font-semibold">ShelfSense Control Panel</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Minimal frontend shell for browsing metadata, running ingestion, and reviewing AI-generated
          insights.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <LoadingState label="Fetching latest pipeline status..." />
        <EmptyState
          title="No books indexed yet"
          description="Run ingestion after placing sample book data in the backend pipeline."
        />
        <ErrorState message="Backend API is unreachable. Check if Django server is running on port 8000." />
      </section>
    </div>
  );
}
