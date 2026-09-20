'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { NAV_LINKS } from '@/lib/site';

/** Desktop + mobile navigation. Marks the current page and closes on navigation / Escape. */
export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  const isActive = (href: string) => (href === '/' ? pathname === '/' : pathname.startsWith(href.split('/').slice(0, 2).join('/')));

  return (
    <>
      <nav aria-label="Main" className="hidden xl:block">
        <ul className="flex items-center gap-1">
          {NAV_LINKS.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                aria-current={isActive(l.href) ? 'page' : undefined}
                className={`whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition ${isActive(l.href) ? 'bg-maroon text-white' : 'text-maroon-dark hover:bg-amber-100'}`}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <button
        type="button"
        className="rounded-md p-2 text-maroon-dark hover:bg-amber-100 xl:hidden"
        aria-label={open ? 'Close menu' : 'Open menu'}
        aria-expanded={open}
        aria-controls="mobile-menu"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>

      {open && (
        <nav id="mobile-menu" aria-label="Main" className="absolute inset-x-0 top-full z-40 border-t border-amber-200 bg-cream shadow-lg xl:hidden">
          <ul className="mx-auto max-w-6xl divide-y divide-amber-100 px-4 py-2">
            {NAV_LINKS.map((l) => (
              <li key={l.href}>
                <Link href={l.href} aria-current={isActive(l.href) ? 'page' : undefined} className={`block py-3 text-base font-medium ${isActive(l.href) ? 'text-maroon' : 'text-gray-800'}`}>
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </>
  );
}
