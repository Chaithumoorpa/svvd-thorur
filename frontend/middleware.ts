import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Only run the locale middleware on the public site. Excluded entirely (not just
  // "un-translated"): /api (the /api/v1/* backend proxy - see next.config.mjs), the
  // admin panel, the devotee/staff auth pages, and the Occasion Blessings flow
  // (public but stays English-only, same reasoning as the auth pages), which all
  // stay outside next-intl's locale routing. Also excluded: Next internals and
  // any request for a file with an extension (favicon.ico, logo.png, robots.txt,
  // sitemap.xml, etc).
  matcher: ['/((?!api|admin|login|register|my-bookings|forgot-password|reset-password|blessings|_next|.*\\..*).*)'],
};
