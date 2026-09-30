'use client';

import { useEffect, useRef, useState } from 'react';

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
const SCRIPT_URL = 'https://challenges.cloudflare.com/turnstile/v0/api.js';

declare global {
  interface Window {
    turnstile?: {
      render: (container: string | HTMLElement, options: Record<string, unknown>) => string;
      remove: (widgetId: string) => void;
    };
  }
}

let scriptPromise: Promise<void> | null = null;
function loadScript(): Promise<void> {
  if (typeof window === 'undefined') return Promise.reject(new Error('no window'));
  if (window.turnstile) return Promise.resolve();
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = SCRIPT_URL;
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Turnstile'));
      document.head.appendChild(script);
    });
  }
  return scriptPromise;
}

/**
 * Cloudflare Turnstile challenge widget. Renders nothing at all when
 * NEXT_PUBLIC_TURNSTILE_SITE_KEY isn't configured - the backend's
 * TurnstileService skips verification the same way, so a form using this
 * still works in any environment that hasn't set Turnstile up yet.
 */
export default function TurnstileWidget({
  onToken, onError,
}: { onToken: (token: string | null) => void; onError?: (failed: boolean) => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);
  const [failed, setFailed] = useState(false);

  const fail = (value: boolean) => {
    setFailed(value);
    onError?.(value);
  };

  useEffect(() => {
    if (!SITE_KEY || !containerRef.current) return;
    let mounted = true;
    loadScript()
      .then(() => {
        if (!mounted || !containerRef.current || !window.turnstile) return;
        widgetId.current = window.turnstile.render(containerRef.current, {
          sitekey: SITE_KEY,
          callback: (token: string) => { fail(false); onToken(token); },
          'expired-callback': () => onToken(null),
          'error-callback': () => fail(true),
        });
      })
      .catch(() => fail(true));
    return () => {
      mounted = false;
      if (widgetId.current && window.turnstile) window.turnstile.remove(widgetId.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!SITE_KEY) return null;
  return (
    <div>
      <div ref={containerRef} />
      {failed && <p className="mt-1 text-xs text-red-600">Security check failed to load. Please refresh the page.</p>}
    </div>
  );
}
