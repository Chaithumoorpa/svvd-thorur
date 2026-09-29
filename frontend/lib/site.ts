import type { Metadata } from 'next';
import { getLocale } from 'next-intl/server';
import { routing } from '@/i18n/routing';
import { fetchTemple } from './server-api';
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

/**
 * Canonical + hreflang alternates for a public page at `path` (e.g. '/timings', '/'
 * for the homepage). Each locale gets a SELF-referencing canonical (its own URL, not
 * always the English one) plus a full cross-reference to every other locale's version
 * of the same page - the standard Google-recommended shape for genuinely translated
 * content, so the language variants read as siblings, not accidental duplicates of
 * each other. Call from a page's own `generateMetadata` with that page's static path.
 */
export async function localizedAlternates(path: string) {
  const locale = await getLocale();
  const clean = path === '/' ? '' : path;
  const urlFor = (loc: string) => `${SITE_URL}${loc === routing.defaultLocale ? '' : `/${loc}`}${clean}`;

  const languages: Record<string, string> = { 'x-default': urlFor(routing.defaultLocale) };
  for (const loc of routing.locales) languages[loc] = urlFor(loc);

  return { canonical: urlFor(locale), languages };
}

/**
 * The Open Graph / Twitter Card image: the temple's own hero image once Admin -> Temple
 * Info has one, otherwise the site logo so link previews always have an image.
 */
export function socialImage(temple: Temple | null, alt: string) {
  return temple?.hero_image_url ? { url: temple.hero_image_url, alt } : { url: '/logo.png', width: 512, height: 512, alt };
}

/**
 * Full per-page Metadata for a public page at `path`: canonical + hreflang alternates
 * (see localizedAlternates) plus a matching Open Graph / Twitter Card. Next.js resolves
 * `openGraph`/`twitter` as a whole object per route segment rather than merging them
 * field-by-field with the parent layout's, so a page that only overrode title/description
 * here would otherwise lose app/layout.tsx's type/siteName/image (falling back to the
 * default Twitter "summary" card with no image) instead of just gaining its own title.
 * Rebuilding the full object per page keeps every page's social preview complete.
 */
export async function pageMetadata(path: string, page?: { title?: string; description?: string }): Promise<Metadata> {
  const [{ canonical, languages }, temple] = await Promise.all([localizedAlternates(path), fetchTemple()]);
  const name = templeName(temple);
  const title = page?.title || name;
  const description = page?.description || temple?.tagline || SITE_FALLBACK.description;
  const image = socialImage(temple, name);

  return {
    ...(page?.title ? { title: page.title } : {}),
    ...(page?.description ? { description: page.description } : {}),
    alternates: { canonical, languages },
    openGraph: { type: 'website', siteName: name, title, description, locale: 'en_IN', url: canonical, images: [image] },
    twitter: { card: 'summary_large_image', title, description, images: [image.url] },
  };
}

/** Google Maps only allows embedding its /maps/embed URLs; anything else is shown as a link. */
export function isEmbeddableMap(url: string | null | undefined): boolean {
  return !!url && /^https:\/\/www\.google\.com\/maps\/embed/.test(url);
}

// `key` maps to a `nav.*` entry in messages/<locale>.json (see SiteHeader / MobileNav / SiteFooter).
export const NAV_LINKS = [
  { href: '/', key: 'home' },
  { href: '/timings', key: 'timings' },
  { href: '/poojas', key: 'poojas' },
  { href: '/festivals', key: 'festivals' },
  { href: '/announcements', key: 'announcements' },
  { href: '/gallery', key: 'gallery' },
  { href: '/about/history', key: 'about' },
  { href: '/contact', key: 'contact' },
] as const;
