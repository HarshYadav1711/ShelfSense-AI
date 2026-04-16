type LoadingStateProps = {
  label?: string;
};

export function LoadingState({ label = "Loading..." }: LoadingStateProps) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-6">
      <div className="mb-3 h-2 w-24 animate-pulse rounded bg-zinc-200" />
      <div className="h-2 w-48 animate-pulse rounded bg-zinc-200" />
      <p className="mt-4 text-sm text-zinc-500">{label}</p>
    </div>
  );
}
