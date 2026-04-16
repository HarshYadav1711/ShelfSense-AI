type ErrorStateProps = {
  title?: string;
  message: string;
};

export function ErrorState({ title = "Something went wrong", message }: ErrorStateProps) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-6" role="alert">
      <h2 className="text-sm font-semibold tracking-tight text-red-900">{title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-red-800">{message}</p>
    </div>
  );
}
