import type { MetadataRoute } from 'next';
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
  { path: '/legal/privacy-policy', priority: 0.2, changeFrequency: 'monthly' },
  { path: '/legal/terms', priority: 0.2, changeFrequency: 'monthly' },
  { path: '/legal/refund-policy', priority: 0.2, changeFrequency: 'monthly' },
];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return ROUTES.map(({ path, priority, changeFrequency }) => ({ url: `${SITE_URL}${path}`, lastModified, priority, changeFrequency }));
}
