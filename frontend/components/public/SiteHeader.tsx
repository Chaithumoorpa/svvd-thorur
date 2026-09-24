import Image from 'next/image';
import { getTranslations } from 'next-intl/server';
import { Phone } from 'lucide-react';
import { Link } from '@/i18n/navigation';
import { fetchTemple } from '@/lib/server-api';
import { templeLocation, templeName } from '@/lib/site';
import AccountNav from './AccountNav';
import LanguageSwitcher from './LanguageSwitcher';
import MobileNav from './MobileNav';

/** Server component: the name/contact come from the temple profile (Admin -> Temple Info). */
export default async function SiteHeader() {
  const temple = await fetchTemple();
  const name = templeName(temple);
  const location = templeLocation(temple);
  const t = await getTranslations('header');

  return (
    <header className="relative z-30 border-b-4 border-saffron bg-cream shadow-sm">
      <div className="bg-maroon-dark text-amber-100">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-1.5 text-xs sm:text-sm">
          <p lang="te" className="truncate font-medium">{t('omPrayer')}</p>
          <div className="flex flex-none items-center gap-3">
            {temple?.contact_phone && (
              <a href={`tel:${temple.contact_phone.replace(/\s/g, '')}`} className="inline-flex items-center gap-1 hover:text-white">
                <Phone className="h-3.5 w-3.5" aria-hidden="true" /> {temple.contact_phone}
              </a>
            )}
            <span className="hidden sm:inline-flex">
              <AccountNav />
            </span>
            <LanguageSwitcher id="lang-switcher-desktop" className="hidden text-amber-100 sm:inline-flex" />
          </div>
        </div>
      </div>

      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="flex min-w-0 items-center gap-3">
          <Image src="/logo.png" alt="" width={52} height={52} priority className="h-11 w-11 flex-none sm:h-[52px] sm:w-[52px]" />
          <span className="min-w-0">
            <span className="block font-serif text-base font-bold leading-tight text-maroon sm:text-xl">{name}</span>
            {location && <span className="block truncate text-xs text-gray-600 sm:text-sm">{location}</span>}
          </span>
        </Link>
        <MobileNav />
      </div>
    </header>
  );
}
