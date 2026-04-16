const navItems = [
  { label: "Dashboard", href: "/" },
  { label: "Books", href: "/books" },
  { label: "Q&A", href: "/qa" },
];

export function AppNav() {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4">
        <p className="text-sm font-semibold text-zinc-900">ShelfSense AI</p>
        <nav className="flex items-center gap-4">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm text-zinc-600 transition hover:text-zinc-900"
            >
              {item.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
