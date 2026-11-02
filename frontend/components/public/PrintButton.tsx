'use client';

import { Printer } from 'lucide-react';

export default function PrintButton({ label }: { label: string }) {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="inline-flex items-center gap-2 rounded-full bg-maroon px-5 py-2.5 font-semibold text-white shadow hover:bg-maroon-dark"
    >
      <Printer className="h-4 w-4" aria-hidden="true" /> {label}
    </button>
  );
}
