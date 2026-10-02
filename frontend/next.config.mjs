import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./i18n/request.ts');

/** @type {import('next').NextConfig} */

// Baseline security headers for every page. (The API sets its own in production.)
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  // camera=(self) allows the admin QR ticket-scanner (getUserMedia) on this origin -
  // still blocked for any third-party iframe. Empty () for camera would block the
  // permission prompt from ever appearing at all, not just deny it silently.
  { key: 'Permissions-Policy', value: 'camera=(self), microphone=(), geolocation=()' },
];

// Legacy / duplicate URLs -> one canonical page each (keeps SEO signals in one place).
const redirects = [
  ['/history', '/about/history'],
  ['/overview', '/about/history'],
  ['/about/overview', '/about/history'],
  ['/about/general-info', '/information'],
  ['/about/timings', '/timings'],
  ['/daily-poojas', '/poojas?type=daily'],
  ['/sevas/daily-poojas', '/poojas?type=daily'],
  ['/festival-sevas', '/poojas?type=festival'],
  ['/sevas/festival-sevas', '/poojas?type=festival'],
  ['/sevas/special-sevas', '/poojas?type=special'],
  ['/support/contact', '/contact'],
  ['/privacy-policy', '/legal/privacy-policy'],
  ['/terms', '/legal/terms'],
  ['/signin', '/login'],
  ['/signup', '/login'],
];

// Public API origin (e.g. https://api.svvdthorur.org). Unset = local dev, where the
// browser goes through the /api/v1 rewrite below to a backend on 127.0.0.1:8000.
const publicApiUrl = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/+$/, '');

// On Vercel there is no backend on localhost: without this the build would succeed
// and every server-rendered page would quietly render its empty "no data" state.
if (process.env.VERCEL && !publicApiUrl) {
  throw new Error('NEXT_PUBLIC_API_URL must be set in the Vercel project (e.g. https://api.svvdthorur.org)');
}

const nextConfig = {
  // Same-origin /api/v1 proxy: what the browser uses in local dev. With
  // NEXT_PUBLIC_API_URL set the browser calls the API directly (lib/api.ts), and
  // this only serves pages still holding a pre-cutover JS bundle.
  async rewrites() {
    const backendUrl =
      process.env.INTERNAL_API_BASE_URL || (publicApiUrl ? `${publicApiUrl}/api/v1` : 'http://127.0.0.1:8000/api/v1');
    return [{ source: '/api/v1/:path*', destination: `${backendUrl}/:path*` }];
  },

  async redirects() {
    return redirects.map(([source, destination]) => ({ source, destination, permanent: true }));
  },

  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },

  // Without this, Next's own trailing-slash normalization redirects BEFORE
  // rewrites are applied, fighting FastAPI's own redirect_slashes (every
  // /api/v1/* route here is registered with a trailing slash) - the two
  // bounce a request between "add slash" and "strip slash" forever. This
  // lets rewritten /api/v1/* requests reach the backend as-is, where at
  // most one real redirect (FastAPI adding the slash) resolves it.
  skipTrailingSlashRedirect: true,

  reactStrictMode: true,
  poweredByHeader: false,
};

export default withNextIntl(nextConfig);
