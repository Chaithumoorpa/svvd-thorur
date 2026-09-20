import Link from 'next/link';
import { Facebook, Instagram, Mail, MapPin, Phone, Youtube } from 'lucide-react';
import { formatTimeRange } from '@/lib/format';
import { fetchTemple, fetchTimings } from '@/lib/server-api';
import { isEmbeddableMap, NAV_LINKS, templeAddress, templeName } from '@/lib/site';
import VisitorCount from './VisitorCount';

export default async function SiteFooter() {
  const [temple, timings] = await Promise.all([fetchTemple(), fetchTimings()]);
  const name = templeName(temple);
  const address = templeAddress(temple);
  const year = new Date().getFullYear();
  const socials = [
    { href: temple?.facebook_url, label: 'Facebook', Icon: Facebook },
    { href: temple?.instagram_url, label: 'Instagram', Icon: Instagram },
    { href: temple?.youtube_url, label: 'YouTube', Icon: Youtube },
  ].filter((s) => s.href);

  return (
    <footer className="bg-maroon-dark text-amber-50">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <h2 className="font-serif text-xl font-bold text-saffron-light">{name}</h2>
          {temple?.tagline && <p className="mt-2 text-sm text-amber-100/80">{temple.tagline}</p>}
          {socials.length > 0 && (
            <ul className="mt-4 flex gap-3">
              {socials.map(({ href, label, Icon }) => (
                <li key={label}>
                  <a href={href!} target="_blank" rel="noopener noreferrer" aria-label={label} className="inline-flex rounded-full bg-white/10 p-2 hover:bg-white/20">
                    <Icon className="h-4 w-4" />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="mb-3 font-semibold text-saffron-light">Darshan Timings</h3>
          {timings.length ? (
            <ul className="space-y-2 text-sm">
              {timings.map((t) => (
                <li key={t.id}>
                  <span className="block text-amber-100/70">{t.label}{t.days !== 'Daily' ? ` (${t.days})` : ''}</span>
                  <span className="font-medium">{formatTimeRange(t.start_time, t.end_time)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-amber-100/70">Timings will be published soon.</p>
          )}
        </div>

        <div>
          <h3 className="mb-3 font-semibold text-saffron-light">Explore</h3>
          <ul className="space-y-2 text-sm">
            {NAV_LINKS.filter((l) => l.href !== '/').map((l) => (
              <li key={l.href}><Link href={l.href} className="hover:text-white hover:underline">{l.label}</Link></li>
            ))}
            <li><Link href="/donations" className="hover:text-white hover:underline">Donations</Link></li>
            <li><Link href="/committee" className="hover:text-white hover:underline">Temple Committee</Link></li>
          </ul>
        </div>

        <div>
          <h3 className="mb-3 font-semibold text-saffron-light">Visit & Contact</h3>
          <ul className="space-y-3 text-sm">
            {address && (
              <li className="flex gap-2"><MapPin className="mt-0.5 h-4 w-4 flex-none text-saffron-light" aria-hidden="true" /><span>{address}</span></li>
            )}
            {temple?.contact_phone && (
              <li className="flex gap-2"><Phone className="mt-0.5 h-4 w-4 flex-none text-saffron-light" aria-hidden="true" /><a href={`tel:${temple.contact_phone.replace(/\s/g, '')}`} className="hover:text-white">{temple.contact_phone}</a></li>
            )}
            {temple?.contact_email && (
              <li className="flex gap-2"><Mail className="mt-0.5 h-4 w-4 flex-none text-saffron-light" aria-hidden="true" /><a href={`mailto:${temple.contact_email}`} className="break-all hover:text-white">{temple.contact_email}</a></li>
            )}
            {temple?.map_url && !isEmbeddableMap(temple.map_url) && (
              <li><a href={temple.map_url} target="_blank" rel="noopener noreferrer" className="font-medium text-saffron-light hover:underline">Get directions →</a></li>
            )}
          </ul>
        </div>
      </div>

      {isEmbeddableMap(temple?.map_url) && (
        <div className="mx-auto max-w-6xl px-4 pb-10">
          <iframe
            title={`Map showing the location of ${name}`}
            src={temple!.map_url!}
            className="h-56 w-full rounded-xl border-0 sm:h-64"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            sandbox="allow-scripts allow-same-origin allow-popups"
          />
        </div>
      )}

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-5 text-xs text-amber-100/70 sm:flex-row">
          <p>© {year} {name}. All rights reserved.</p>
          <VisitorCount />
          <nav aria-label="Legal" className="flex gap-4">
            <Link href="/legal/privacy-policy" className="hover:text-white">Privacy</Link>
            <Link href="/legal/terms" className="hover:text-white">Terms</Link>
            <Link href="/legal/refund-policy" className="hover:text-white">Refunds</Link>
            <Link href="/login" className="hover:text-white">Staff login</Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
