import { defineRouting } from 'next-intl/routing';

/**
 * Locales for the PUBLIC site only (app/[locale]/(public)/*). The admin panel,
 * /login, /forgot-password and /reset-password are outside this [locale] segment
 * and always render in English, unaffected by this config.
 *
 * localePrefix: 'as-needed' keeps every existing English URL exactly as it is today
 * (e.g. `/`, `/timings`, `/poojas`) - no `/en` prefix - while other locales are
 * prefixed (`/te/timings`, `/ta/poojas`, `/kn`, `/hi/gallery`, ...).
 */
export const routing = defineRouting({
  locales: ['en', 'te', 'ta', 'kn', 'hi'],
  defaultLocale: 'en',
  localePrefix: 'as-needed',
});

export type AppLocale = (typeof routing.locales)[number];
