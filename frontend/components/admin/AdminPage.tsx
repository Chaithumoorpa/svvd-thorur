import type { ReactNode } from 'react';

interface AdminPageProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}

/** Consistent page frame for every admin screen. */
export default function AdminPage({ title, description, actions, children }: AdminPageProps) {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-12 pt-16 sm:px-6 lg:pt-8">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </header>
      {children}
    </div>
  );
}

export function StatusPill({ on, onLabel = 'Active', offLabel = 'Hidden' }: { on: boolean; onLabel?: string; offLabel?: string }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        on ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
      }`}
    >
      {on ? onLabel : offLabel}
    </span>
  );
}
