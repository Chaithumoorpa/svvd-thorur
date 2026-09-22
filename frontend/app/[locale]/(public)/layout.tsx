import { getTranslations } from 'next-intl/server';
import SiteFooter from '@/components/public/SiteFooter';
import SiteHeader from '@/components/public/SiteHeader';
import VisitorTracker from '@/components/VisitorTracker';

export default async function PublicLayout({ children }: { children: React.ReactNode }) {
  const t = await getTranslations('common');
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:text-maroon"
      >
        {t('skipToContent')}
      </a>
      <VisitorTracker />
      <SiteHeader />
      <main id="main" className="flex-1">
        {children}
      </main>
      <SiteFooter />
    </>
  );
}
