'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { Languages } from 'lucide-react';
import { usePathname, useRouter } from '@/i18n/navigation';
import { routing, type AppLocale } from '@/i18n/routing';

/**
 * Swaps the locale segment of the current path client-side, keeping the same page
 * (and query string, e.g. /poojas?type=daily) in the new language. Used in
 * SiteHeader (desktop) and MobileNav (mobile menu).
 */
export default function LanguageSwitcher({ id, className }: { id?: string; className?: string }) {
  const t = useTranslations('language');
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const nextLocale = event.target.value as AppLocale;
    const query = searchParams.toString();
    router.replace(`${pathname}${query ? `?${query}` : ''}`, { locale: nextLocale });
  };

  return (
    <label className={`inline-flex items-center gap-1.5 ${className ?? ''}`}>
      <Languages className="h-4 w-4 flex-none" aria-hidden="true" />
      <span className="sr-only">{t('label')}</span>
      <select
        id={id}
        value={locale}
        onChange={handleChange}
        aria-label={t('label')}
        className="cursor-pointer rounded-md border-0 bg-transparent py-1 pl-1 pr-6 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-saffron"
      >
        {routing.locales.map((loc) => (
          <option key={loc} value={loc} className="text-gray-900">
            {t(loc)}
          </option>
        ))}
      </select>
    </label>
  );
}
