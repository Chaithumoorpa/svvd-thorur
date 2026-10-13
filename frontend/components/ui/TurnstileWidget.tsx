'use client';

import { useEffect, useRef, useState } from 'react';

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
const SCRIPT_URL = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
// Silent retries after a failed challenge before asking the visitor to act.
// Mobile data drops and slow responses are common causes of one-off failures.
const RETRY_DELAYS_MS = [1500, 4000];

declare global {
  interface Window {
    turnstile?: {
      render: (container: string | HTMLElement, options: Record<string, unknown>) => string;
      reset: (widgetId: string) => void;
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
      script.onerror = () => {
        script.remove();
        scriptPromise = null; // let "Try again" load it afresh
        reject(new Error('Failed to load Turnstile'));
      };
      document.head.appendChild(script);
    });
  }
  return scriptPromise;
}

type Status = 'pending' | 'retrying' | 'failed' | 'ok';

/**
 * Cloudflare Turnstile challenge widget. Renders nothing at all when
 * NEXT_PUBLIC_TURNSTILE_SITE_KEY isn't configured - the backend's
 * TurnstileService skips verification the same way, so a form using this
 * still works in any environment that hasn't set Turnstile up yet.
 *
 * Failed challenges are retried here (not by Turnstile's own auto-retry) so the
 * widget knows when it has really given up. Only then does it report `onError(true)`
 * and offer a Try again button. Reloading the page would wipe the form.
 */
export default function TurnstileWidget({
  onToken, onError,
}: { onToken: (token: string | null) => void; onError?: (failed: boolean) => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);
  const attempts = useRef(0);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const mounted = useRef(true);
  const [status, setStatus] = useState<Status>('pending');
  const [errorCode, setErrorCode] = useState<string | null>(null);

  const giveUp = (code: string | null) => {
    setErrorCode(code);
    setStatus('failed');
    onError?.(true);
  };

  const handleFailure = (code: string | null) => {
    onToken(null);
    const delay = RETRY_DELAYS_MS[attempts.current];
    if (delay === undefined) {
      giveUp(code);
      return;
    }
    attempts.current += 1;
    setStatus('retrying');
    retryTimer.current = setTimeout(() => {
      if (mounted.current && widgetId.current && window.turnstile) window.turnstile.reset(widgetId.current);
    }, delay);
  };

  const renderWidget = () => {
    loadScript()
      .then(() => {
        if (!mounted.current || !containerRef.current || !window.turnstile || widgetId.current) return;
        widgetId.current = window.turnstile.render(containerRef.current, {
          sitekey: SITE_KEY,
          retry: 'never',
          callback: (token: string) => {
            attempts.current = 0;
            setStatus('ok');
            setErrorCode(null);
            onError?.(false);
            onToken(token);
          },
          // refresh-expired / refresh-timeout default to "auto": Turnstile re-solves
          // by itself and calls `callback` again, so only drop the stale token here.
          'expired-callback': () => onToken(null),
          'timeout-callback': () => onToken(null),
          'error-callback': (code: string | number) => {
            handleFailure(code == null ? null : String(code));
            return true; // handled - don't also log to the console
          },
        });
      })
      .catch(() => mounted.current && giveUp(null));
  };

  const tryAgain = () => {
    attempts.current = 0;
    setErrorCode(null);
    setStatus('retrying');
    onError?.(false);
    if (widgetId.current && window.turnstile) window.turnstile.reset(widgetId.current);
    else renderWidget();
  };

  useEffect(() => {
    if (!SITE_KEY) return;
    mounted.current = true;
    renderWidget();
    return () => {
      mounted.current = false;
      clearTimeout(retryTimer.current);
      if (widgetId.current && window.turnstile) window.turnstile.remove(widgetId.current);
      widgetId.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!SITE_KEY) return null;
  return (
    <div>
      <div ref={containerRef} />
      {status === 'retrying' && <p className="mt-1 text-xs text-gray-500">Security check didn&apos;t complete, retrying…</p>}
      {status === 'failed' && (
        <div className="mt-1 text-xs text-red-600" role="alert">
          <p>
            Security check couldn&apos;t be completed{errorCode ? ` (code ${errorCode})` : ''}.{' '}
            <button type="button" onClick={tryAgain} className="font-semibold underline">Try again</button>
          </p>
          <p className="mt-0.5 text-gray-600">
            On mobile data, switching to Wi-Fi or turning off any VPN or data saver usually fixes this.
          </p>
        </div>
      )}
    </div>
  );
}
