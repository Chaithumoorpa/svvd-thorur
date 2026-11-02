const STORAGE_KEY = 'svvd_cookie_consent';
export const COOKIE_CONSENT_MANAGE_EVENT = 'cookie-consent:manage';

export type CookieConsentStatus = 'accepted' | 'declined';

interface StoredConsent {
  status: CookieConsentStatus;
  at: string;
}

/** Wrapped in try/catch throughout - private browsing / blocked storage must
 * not break the page, it should just behave as if no choice was ever made. */
export function getCookieConsent(): CookieConsentStatus | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return (JSON.parse(raw) as StoredConsent).status ?? null;
  } catch {
    return null;
  }
}

export function setCookieConsent(status: CookieConsentStatus): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ status, at: new Date().toISOString() }));
  } catch {
    /* storage unavailable - the choice just won't persist across visits */
  }
}

export function clearCookieConsent(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* nothing to do */
  }
}
