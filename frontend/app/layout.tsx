import type { Metadata, Viewport } from 'next';
import { getLocale } from 'next-intl/server';
import './globals.css';
import { fetchTemple } from '@/lib/server-api';
import { SITE_FALLBACK, SITE_URL, templeName } from '@/lib/site';

// Public pages read live data from the API (cached per-request via fetch revalidate), so nothing
// is frozen at build time when the backend is not reachable.
export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const temple = await fetchTemple();
  const name = templeName(temple);
  const description = temple?.tagline || SITE_FALLBACK.description;
  return {
    metadataBase: new URL(SITE_URL),
    title: { default: name, template: `%s | ${name}` },
    description,
    applicationName: name,
    openGraph: {
      type: 'website',
      siteName: name,
      title: name,
      description,
      locale: 'en_IN',
      ...(temple?.hero_image_url ? { images: [{ url: temple.hero_image_url }] } : {}),
    },
    twitter: { card: 'summary_large_image', title: name, description },
    robots: { index: true, follow: true },
  };
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#7a1c1c',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Falls back to 'en' for routes outside the [locale] segment (admin, login,
  // forgot-password, reset-password), which the i18n middleware never touches.
  const locale = await getLocale();
  return (
    <html lang={locale}>
      <body className="flex min-h-screen flex-col bg-cream text-templeDark antialiased">{children}</body>
    </html>
  );
}
