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

const nextConfig = {
  // Proxy /api/v1 requests to the backend
  async rewrites() {
    const backendUrl = process.env.INTERNAL_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
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

  // Output configuration for Docker
  output: 'standalone',
};

export default withNextIntl(nextConfig);
