import type { Temple } from './types';

/**
 * Defaults used ONLY when the backend has no temple profile yet (or is unreachable).
 * The real name, address, contact details and timings are managed in Admin -> Temple Info.
 */
export const SITE_FALLBACK = {
  name: 'Temple',
  description: 'Official website of the temple: darshan timings, poojas, festivals and announcements.',
} as const;

/** Public site origin used for canonical URLs, sitemap and Open Graph tags. */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000').replace(/\/$/, '');

export function templeName(temple: Temple | null): string {
  return temple?.name || SITE_FALLBACK.name;
}

export function templeLocation(temple: Temple | null): string {
  if (!temple) return '';
  return [temple.village, temple.district, temple.state].filter(Boolean).join(', ');
}

export function templeAddress(temple: Temple | null): string {
  if (!temple) return '';
  return [temple.address, temple.village, temple.district, temple.state, temple.pincode].filter(Boolean).join(', ');
}

/** Google Maps only allows embedding its /maps/embed URLs; anything else is shown as a link. */
export function isEmbeddableMap(url: string | null | undefined): boolean {
  return !!url && /^https:\/\/www\.google\.com\/maps\/embed/.test(url);
}

export const NAV_LINKS = [
  { href: '/', label: 'Home' },
  { href: '/timings', label: 'Timings' },
  { href: '/poojas', label: 'Poojas & Sevas' },
  { href: '/festivals', label: 'Festivals' },
  { href: '/announcements', label: 'Announcements' },
  { href: '/gallery', label: 'Gallery' },
  { href: '/about/history', label: 'About' },
  { href: '/contact', label: 'Contact' },
] as const;
