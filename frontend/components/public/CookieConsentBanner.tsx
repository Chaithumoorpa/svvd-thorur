'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { COOKIE_CONSENT_MANAGE_EVENT, getCookieConsent, setCookieConsent } from '@/lib/cookieConsent';
import { btnGhost, btnPrimary } from '@/components/ui/styles';

/** Site-wide accept/decline banner. Nothing optional is set on this site today
 * (see the Cookie Policy) - this exists so the choice is on record and ready
 * to gate anything optional we might add later, and because donors outside
 * India (US/UK) expect the notice regardless. */
export default function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);
  const t = useTranslations('cookieConsent');

  useEffect(() => {
    setVisible(getCookieConsent() === null);
    const reopen = () => setVisible(true);
    window.addEventListener(COOKIE_CONSENT_MANAGE_EVENT, reopen);
    return () => window.removeEventListener(COOKIE_CONSENT_MANAGE_EVENT, reopen);
  }, []);

  if (!visible) return null;

  function choose(status: 'accepted' | 'declined') {
    setCookieConsent(status);
    setVisible(false);
  }

  return (
    <div
      role="region"
      aria-label={t('policyLinkText')}
      className="fixed inset-x-0 bottom-0 z-50 border-t border-amber-200 bg-white/95 px-4 py-4 shadow-[0_-2px_10px_rgba(0,0,0,0.08)] backdrop-blur"
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 sm:flex-row sm:justify-between">
        <p className="text-sm text-gray-700">
          {t('message')}{' '}
          <Link href="/legal/cookie-policy" className="font-medium text-maroon hover:underline">
            {t('policyLinkText')}
          </Link>
        </p>
        <div className="flex flex-none gap-2">
          <button type="button" className={btnGhost} onClick={() => choose('declined')}>
            {t('decline')}
          </button>
          <button type="button" className={btnPrimary} onClick={() => choose('accepted')}>
            {t('accept')}
          </button>
        </div>
      </div>
    </div>
  );
}
