import Link from 'next/link';
import { CalendarDays, Clock, HandHeart, MapPin, Megaphone, Sparkles } from 'lucide-react';
import DeityCarousel from '@/components/DeityCarousel';
import JsonLd from '@/components/public/JsonLd';
import SectionHeading from '@/components/public/SectionHeading';
import { formatDate, formatTime, formatTimeRange, parseDate } from '@/lib/format';
import { fetchHome } from '@/lib/server-api';
import { SITE_URL, templeAddress, templeName } from '@/lib/site';


const HH_MM = (t: string) => t.slice(0, 5);

export default async function HomePage() {
  const { temple, timings, announcements, festivals, poojas } = await fetchHome();
  const name = templeName(temple);
  const address = templeAddress(temple);

  const jsonLd: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'HinduTemple',
    name,
    url: SITE_URL,
    ...(temple?.tagline ? { description: temple.tagline } : {}),
    ...(address ? { address: { '@type': 'PostalAddress', streetAddress: address, addressCountry: 'IN' } } : {}),
    ...(temple?.contact_phone ? { telephone: temple.contact_phone } : {}),
    ...(temple?.hero_image_url ? { image: temple.hero_image_url } : {}),
    ...(timings.length
      ? {
          openingHoursSpecification: timings.map((t) => ({
            '@type': 'OpeningHoursSpecification',
            dayOfWeek: t.days.toLowerCase() === 'daily' ? ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] : undefined,
            opens: HH_MM(t.start_time),
            closes: HH_MM(t.end_time),
          })),
        }
      : {}),
  };

  return (
    <div className="bg-cream">
      <JsonLd data={jsonLd} />

      <section aria-label="Presiding deities">
        <DeityCarousel />
      </section>

      {/* Darshan timings strip */}
      <section aria-labelledby="darshan-heading" className="border-y-2 border-saffron/40 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-5 sm:flex-row sm:items-center sm:justify-between">
          <h2 id="darshan-heading" className="flex items-center gap-2 font-serif text-xl font-bold text-maroon">
            <Clock className="h-5 w-5 text-saffron" aria-hidden="true" /> Darshan Timings
          </h2>
          {timings.length ? (
            <ul className="flex flex-wrap gap-x-8 gap-y-2">
              {timings.map((t) => (
                <li key={t.id} className="text-sm">
                  <span className="text-gray-500">{t.label}</span>
                  <span className="ml-2 font-semibold text-gray-900">{formatTimeRange(t.start_time, t.end_time)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Timings will be announced soon.</p>
          )}
          <Link href="/timings" className="text-sm font-semibold text-saffron hover:underline">Full schedule →</Link>
        </div>
      </section>

      {/* Announcements */}
      <section aria-labelledby="ann-heading" className="mx-auto max-w-6xl px-4 py-14">
        <SectionHeading title="Announcements" subtitle="The latest news from the temple" href="/announcements" />
        <span id="ann-heading" className="sr-only">Latest announcements</span>
        {announcements.length ? (
          <div className="grid gap-6 md:grid-cols-3">
            {announcements.map((a) => (
              <article key={a.id} className="rounded-xl border-l-4 border-saffron bg-white p-6 shadow-sm">
                <p className="mb-2 flex items-center gap-1.5 text-xs text-gray-500">
                  <Megaphone className="h-3.5 w-3.5" aria-hidden="true" />
                  <time dateTime={(a.start_date ?? a.created_at).slice(0, 10)}>{formatDate(a.start_date ?? a.created_at)}</time>
                </p>
                <h3 className="font-serif text-lg font-bold text-maroon-dark">{a.title}</h3>
                {a.message && <p className="mt-2 line-clamp-3 text-sm text-gray-600">{a.message}</p>}
              </article>
            ))}
          </div>
        ) : (
          <p className="text-center italic text-gray-500">No announcements at the moment.</p>
        )}
      </section>

      {/* Festivals */}
      <section aria-labelledby="fest-heading" className="bg-white py-14">
        <div className="mx-auto max-w-6xl px-4">
          <SectionHeading title="Upcoming Festivals" subtitle="Join us in the celebrations" href="/festivals" />
          <span id="fest-heading" className="sr-only">Upcoming festivals</span>
          {festivals.length ? (
            <div className="grid gap-6 md:grid-cols-3">
              {festivals.map((f) => {
                const d = f.festival_date ? parseDate(f.festival_date) : null;
                return (
                  <article key={f.id} className="overflow-hidden rounded-xl border border-amber-100 bg-cream shadow-sm">
                    <div className="flex items-center gap-4 bg-maroon px-5 py-4 text-white">
                      <div className="text-center leading-none">
                        <span className="block font-serif text-3xl font-bold">{d ? d.getDate() : '—'}</span>
                        <span className="text-xs uppercase tracking-wider text-amber-200">{d ? d.toLocaleString('en-IN', { month: 'short' }) : 'TBD'}</span>
                      </div>
                      <h3 className="font-serif text-lg font-bold">{f.name}</h3>
                    </div>
                    <div className="p-5">
                      {f.location && <p className="mb-1 flex items-center gap-1 text-xs text-gray-500"><MapPin className="h-3 w-3" aria-hidden="true" />{f.location}</p>}
                      {f.description && <p className="line-clamp-3 text-sm text-gray-600">{f.description}</p>}
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="text-center italic text-gray-500">No upcoming festivals right now. Please check back soon.</p>
          )}
        </div>
      </section>

      {/* Rituals */}
      <section aria-labelledby="rituals-heading" className="bg-gradient-to-b from-maroon to-maroon-dark py-16 text-white">
        <div className="mx-auto max-w-6xl px-4 text-center">
          <h2 id="rituals-heading" className="font-serif text-3xl font-bold italic sm:text-4xl">Daily Rituals & Sevas</h2>
          <p className="mx-auto mt-2 max-w-xl text-amber-100">Offer your prayers through the temple's daily poojas and special sevas.</p>
          {poojas.length ? (
            <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {poojas.map((p) => (
                <li key={p.id} className="rounded-xl bg-white/10 p-6 backdrop-blur-sm">
                  <Sparkles className="mx-auto mb-3 h-7 w-7 text-saffron-light" aria-hidden="true" />
                  <h3 className="font-serif text-lg font-bold">{p.name}</h3>
                  <p className="mt-1 text-sm text-saffron-light">{p.start_time ? formatTime(p.start_time) : 'Anytime'}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-8 italic text-amber-100">Rituals will be listed soon.</p>
          )}
          <Link href="/poojas" className="mt-10 inline-block rounded-full bg-saffron px-8 py-3 font-bold text-white shadow hover:bg-saffron-light hover:text-maroon-dark">
            View all poojas & sevas
          </Link>
        </div>
      </section>

      {/* Ways to help */}
      <section aria-label="Ways to participate" className="mx-auto grid max-w-6xl gap-6 px-4 py-14 md:grid-cols-3">
        {[
          { href: '/poojas', icon: Sparkles, title: 'Book a Seva', text: 'Reserve a free seva for you and your family.' },
          { href: '/donations', icon: HandHeart, title: 'Support the Temple', text: 'Contribute to annadanam, festivals and upkeep.' },
          { href: '/contact', icon: CalendarDays, title: 'Plan Your Visit', text: 'Timings, directions and how to reach us.' },
        ].map(({ href, icon: Icon, title, text }) => (
          <Link key={href} href={href} className="group rounded-xl border border-amber-200 bg-white p-6 text-center shadow-sm transition hover:-translate-y-0.5 hover:border-saffron hover:shadow-md">
            <Icon className="mx-auto mb-3 h-8 w-8 text-saffron" aria-hidden="true" />
            <h3 className="font-serif text-lg font-bold text-maroon group-hover:underline">{title}</h3>
            <p className="mt-1 text-sm text-gray-600">{text}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
