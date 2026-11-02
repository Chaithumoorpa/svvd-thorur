import { fetchTemple } from '@/lib/server-api';
import { SITE_FALLBACK, SITE_URL, templeLocation, templeName } from '@/lib/site';

export const dynamic = 'force-dynamic';

// llms.txt (see https://llmstxt.org) - a curated, plain-text map of the site for
// LLMs/AI crawlers, mirroring app/sitemap.ts's route list but with a short note
// on what each page actually contains instead of just a URL. Next.js serves this
// route at the literal path /llms.txt because the folder is named that.
export async function GET() {
  const temple = await fetchTemple();
  const name = templeName(temple);
  const location = templeLocation(temple);
  const summary = temple?.tagline || SITE_FALLBACK.description;

  const lines = [
    `# ${name}`,
    '',
    `> ${summary}`,
    '',
    `Official website of ${name}${location ? ` in ${location}` : ''}: darshan timings, poojas and sevas (with online booking), the festival calendar, announcements, donations and devotee accounts. Available in English, Telugu, Hindi, Kannada and Tamil - add /te, /hi, /kn or /ta after the domain for those languages; English is unprefixed.`,
    '',
    '## Pages',
    '',
    `- [Darshan Timings](${SITE_URL}/timings): Daily darshan and pooja timings.`,
    `- [Poojas & Sevas](${SITE_URL}/poojas): Daily poojas, festival sevas and special sevas, with timings and fees; devotees can book online.`,
    `- [Festivals & Events](${SITE_URL}/festivals): Annual festivals, utsavams and special events, with an auto-generated Hindu calendar.`,
    `- [Announcements](${SITE_URL}/announcements): Latest news, notices and updates from the temple.`,
    `- [History](${SITE_URL}/about/history): The history and significance of the temple.`,
    `- [Temple Committee](${SITE_URL}/committee): The trustees and office bearers who serve the temple.`,
    `- [Gallery](${SITE_URL}/gallery): Photographs of the temple, festivals and events.`,
    `- [Donations](${SITE_URL}/donations): How to donate to the temple.`,
    `- [Contact](${SITE_URL}/contact): Address, phone, email and a contact form.`,
    '',
    '## Optional',
    '',
    `- [Privacy Policy](${SITE_URL}/legal/privacy-policy)`,
    `- [Terms and Conditions](${SITE_URL}/legal/terms)`,
    `- [Refund & Cancellation Policy](${SITE_URL}/legal/refund-policy)`,
    '',
  ];

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
}
