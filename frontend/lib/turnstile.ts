/** Pure decision behind every Turnstile-gated form's submit button: never
 * block when the widget isn't configured at all (matches the backend's own
 * no-op-when-unconfigured behavior), otherwise require a live, unconsumed
 * token and no widget error - a stale token or a widget that failed to load
 * must not let the button stay enabled just because one was solved earlier. */
export function isTurnstileBlocked(required: boolean, token: string | null, failed: boolean): boolean {
  return required && (failed || !token);
}
