type LoadingStateProps = {
  label?: string;
  /** `grid` mirrors the books list layout (two columns of card skeletons). */
  variant?: "default" | "grid";
};

function SkeletonBar({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-zinc-200 ${className ?? ""}`} />;
}

export function LoadingState({ label = "Loading...", variant = "default" }: LoadingStateProps) {
  if (variant === "grid") {
    return (
      <section aria-busy="true" aria-label={label} className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <SkeletonBar className="h-4 w-40" />
          <SkeletonBar className="hidden h-4 w-24 sm:block" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card-interactive p-5">
              <SkeletonBar className="h-4 w-[85%] max-w-[14rem]" />
              <SkeletonBar className="mt-3 h-3 w-1/3 max-w-[6rem]" />
              <SkeletonBar className="mt-4 h-3 w-full" />
              <SkeletonBar className="mt-2 h-3 w-5/6" />
              <SkeletonBar className="mt-2 h-3 w-2/3" />
              <div className="mt-5 flex justify-between">
                <SkeletonBar className="h-3 w-16" />
                <SkeletonBar className="h-3 w-20" />
              </div>
            </div>
          ))}
        </div>
        <p className="text-center text-sm text-zinc-500">{label}</p>
      </section>
    );
  }

  return (
    <div className="rounded-md border border-zinc-200 bg-white p-6" aria-busy="true" aria-label={label}>
      <SkeletonBar className="mb-3 h-2 w-24" />
      <SkeletonBar className="h-2 w-48" />
      <SkeletonBar className="mt-4 h-2 w-full max-w-md" />
      <p className="mt-5 text-sm text-zinc-500">{label}</p>
    </div>
  );
}
