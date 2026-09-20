import type { CommitteeMember, Festival, GalleryItem, HomePayload, Pooja, Temple, TempleTiming, Announcement } from './types';

/**
 * Server-side (React Server Component) data access for the public site.
 * Talks to the backend directly and lets Next cache responses, so public pages are
 * server-rendered (good for SEO and speed) instead of fetching after hydration.
 */
const BASE =
  process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL_SERVER || 'http://backend:8000/api/v1';

export const PUBLIC_REVALIDATE_SECONDS = 60;

async function get<T>(path: string, fallback: T, revalidate = PUBLIC_REVALIDATE_SECONDS): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, { next: { revalidate }, headers: { Accept: 'application/json' } });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    // Backend unreachable (e.g. during a docker build): render the page's empty state.
    return fallback;
  }
}

export const fetchHome = () =>
  get<HomePayload>('/public/home', { temple: null, timings: [], announcements: [], festivals: [], poojas: [] });
export const fetchTemple = () => get<Temple | null>('/temple/', null);
export const fetchTimings = () => get<TempleTiming[]>('/temple/timings', []);
export const fetchAnnouncements = () => get<Announcement[]>('/announcements/', []);
export const fetchFestivals = () => get<Festival[]>('/festivals/', []);
export const fetchPoojas = () => get<Pooja[]>('/poojas/', []);
export const fetchGallery = () => get<GalleryItem[]>('/gallery/?page_size=200', []);
export const fetchCommittee = () => get<CommitteeMember[]>('/public/committee', []);
