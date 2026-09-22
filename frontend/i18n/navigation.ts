import { createNavigation } from 'next-intl/navigation';
import { routing } from './routing';

/**
 * Locale-aware Link / useRouter / usePathname / redirect / getPathname, scoped to
 * `routing` above. Anything inside app/[locale]/(public) that links to another
 * public page should import these instead of next/link or next/navigation, so the
 * locale segment (when one applies) is preserved automatically.
 */
export const { Link, redirect, usePathname, useRouter, getPathname } = createNavigation(routing);
