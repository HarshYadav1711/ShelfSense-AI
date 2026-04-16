type EmptyStateProps = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-md border border-dashed border-zinc-300 bg-zinc-50/50 p-8 text-center">
      <h2 className="text-base font-semibold tracking-tight text-zinc-900">{title}</h2>
      <p className="mt-2 text-pretty text-sm leading-relaxed text-zinc-600">{description}</p>
    </div>
  );
}
