'use client';

import { COOKIE_CONSENT_MANAGE_EVENT } from '@/lib/cookieConsent';

/** Reopens the cookie consent banner so a visitor can change an earlier choice. */
export default function CookiePreferencesLink({ label }: { label: string }) {
  return (
    <button
      type="button"
      className="hover:text-white"
      onClick={() => window.dispatchEvent(new Event(COOKIE_CONSENT_MANAGE_EVENT))}
    >
      {label}
    </button>
  );
}
