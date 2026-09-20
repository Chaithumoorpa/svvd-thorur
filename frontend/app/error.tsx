'use client';

import { useEffect } from 'react';

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(error);
  }, [error]);

  return (
    <main role="alert" className="flex flex-1 flex-col items-center justify-center bg-cream px-4 py-24 text-center">
      <h1 className="font-serif text-2xl font-bold text-maroon">Something went wrong</h1>
      <p className="mt-2 max-w-md text-gray-600">We could not load this page. Please try again in a moment.</p>
      <button type="button" onClick={reset} className="mt-6 rounded-full bg-maroon px-6 py-2 font-semibold text-white hover:bg-maroon-dark">
        Try again
      </button>
    </main>
  );
}
