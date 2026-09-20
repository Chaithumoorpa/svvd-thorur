/** Decorative temple-style divider (a lotus between two rules). Purely visual. */
export default function Ornament({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center gap-3 text-saffron ${className}`} aria-hidden="true">
      <span className="h-px w-16 bg-gradient-to-r from-transparent to-saffron/60" />
      <svg width="28" height="28" viewBox="0 0 32 32" fill="currentColor">
        <path d="M16 3c2 4 2 8 0 12-2-4-2-8 0-12zM16 29c2-4 2-8 0-12-2 4-2 8 0 12zM3 16c4-2 8-2 12 0-4 2-8 2-12 0zM29 16c-4-2-8-2-12 0 4 2 8 2 12 0z" opacity=".85" />
        <circle cx="16" cy="16" r="2.6" />
      </svg>
      <span className="h-px w-16 bg-gradient-to-l from-transparent to-saffron/60" />
    </div>
  );
}
