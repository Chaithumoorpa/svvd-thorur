import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Only run the locale middleware on the public site. Excluded entirely (not just
  // "un-translated"): /api (the /api/v1/* backend proxy - see next.config.mjs), the
  // admin panel, and the two auth flows that stay English-only. Also excluded:
  // Next internals and any request for a file with an extension (favicon.ico,
  // logo.png, robots.txt, sitemap.xml, etc).
  matcher: ['/((?!api|admin|login|forgot-password|reset-password|_next|.*\\..*).*)'],
};
