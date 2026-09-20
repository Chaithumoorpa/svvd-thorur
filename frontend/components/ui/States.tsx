import type { ReactNode } from 'react';
import { AlertTriangle, Inbox, Loader2 } from 'lucide-react';
import { btnGhost } from './styles';

export function LoadingBlock({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex items-center justify-center gap-3 py-16 text-gray-500">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="mx-auto my-8 max-w-md rounded-xl border border-red-200 bg-red-50 p-6 text-center">
      <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-red-600" aria-hidden="true" />
      <p className="text-sm text-red-800">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className={`${btnGhost} mt-4`}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyBlock({
  title,
  hint,
  action,
  icon,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="mx-auto my-8 max-w-md rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center">
      <div className="mx-auto mb-3 flex justify-center text-gray-300" aria-hidden="true">
        {icon ?? <Inbox className="h-10 w-10" />}
      </div>
      <h3 className="font-semibold text-gray-700">{title}</h3>
      {hint && <p className="mt-1 text-sm text-gray-500">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/** Success / error banner for form results. */
export function Notice({ kind, children }: { kind: 'success' | 'error'; children: ReactNode }) {
  const cls = kind === 'success' ? 'border-green-200 bg-green-50 text-green-800' : 'border-red-200 bg-red-50 text-red-800';
  return (
    <div role={kind === 'error' ? 'alert' : 'status'} className={`rounded-lg border px-4 py-3 text-sm ${cls}`}>
      {children}
    </div>
  );
}
