'use client';

import { useEffect, useId, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}

/** Accessible dialog: Esc closes, focus moves inside and returns to the trigger, scroll is locked. */
export default function Modal({ title, onClose, children, wide }: ModalProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  // callers pass inline handlers; keep the latest in a ref so the effect below runs once per open
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    // focus the first form control (not the header's close button); fall back to any button
    const first =
      panelRef.current?.querySelector<HTMLElement>('input:not([type=hidden]), select, textarea') ??
      panelRef.current?.querySelector<HTMLElement>('button');
    first?.focus();

    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCloseRef.current();
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = overflow;
      previouslyFocused?.focus?.();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4" onMouseDown={onClose}>
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(e) => e.stopPropagation()}
        className={`max-h-[92vh] w-full overflow-y-auto rounded-t-2xl bg-white shadow-xl sm:rounded-2xl ${wide ? 'sm:max-w-2xl' : 'sm:max-w-lg'}`}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-gray-100 bg-white px-5 py-4">
          <h2 id={titleId} className="text-lg font-semibold text-gray-900">
            {title}
          </h2>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded-lg p-1 text-gray-500 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
