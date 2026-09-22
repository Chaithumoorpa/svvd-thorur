import type { MetadataRoute } from 'next';
import { routing } from '@/i18n/routing';
import { SITE_URL } from '@/lib/site';

export const revalidate = 3600;

const ROUTES: Array<{ path: string; priority: number; changeFrequency: 'daily' | 'weekly' | 'monthly' }> = [
  { path: '/', priority: 1, changeFrequency: 'daily' },
  { path: '/timings', priority: 0.9, changeFrequency: 'monthly' },
  { path: '/poojas', priority: 0.8, changeFrequency: 'weekly' },
  { path: '/festivals', priority: 0.8, changeFrequency: 'weekly' },
  { path: '/announcements', priority: 0.7, changeFrequency: 'daily' },
  { path: '/gallery', priority: 0.6, changeFrequency: 'weekly' },
  { path: '/about/history', priority: 0.6, changeFrequency: 'monthly' },
  { path: '/committee', priority: 0.5, changeFrequency: 'monthly' },
  { path: '/information', priority: 0.5, changeFrequency: 'monthly' },
  { path: '/donations', priority: 0.5, changeFrequency: 'monthly' },
  { path: '/contact', priority: 0.7, changeFrequency: 'monthly' },
  { path: '/media', priority: 0.3, changeFrequency: 'monthly' },
  { path: '/support/feedback', priority: 0.3, changeFrequency: 'monthly' },
  { path: '/support/help-desk', priority: 0.3, changeFrequency: 'monthly' },
  { path: '/legal/privacy-policy', priority: 0.2, changeFrequency: 'monthly' },
  { path: '/legal/terms', priority: 0.2, changeFrequency: 'monthly' },
  { path: '/legal/refund-policy', priority: 0.2, changeFrequency: 'monthly' },
];

function urlFor(path: string, locale: string): string {
  const clean = path === '/' ? '' : path;
  return `${SITE_URL}${locale === routing.defaultLocale ? '' : `/${locale}`}${clean}`;
}

// One <url> entry per route PER LOCALE, each carrying the full set of hreflang
// alternates (including itself + x-default) - the shape Google's own docs
// recommend for a sitemap covering translated content, and a stronger signal
// than per-page <link rel="alternate"> tags alone for a new/unindexed site.
export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  const entries: MetadataRoute.Sitemap = [];

  for (const { path, priority, changeFrequency } of ROUTES) {
    const languages: Record<string, string> = { 'x-default': urlFor(path, routing.defaultLocale) };
    for (const loc of routing.locales) languages[loc] = urlFor(path, loc);

    for (const loc of routing.locales) {
      entries.push({ url: urlFor(path, loc), lastModified, priority, changeFrequency, alternates: { languages } });
    }
  }

  return entries;
}
