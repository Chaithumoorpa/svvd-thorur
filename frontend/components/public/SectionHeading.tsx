import Link from 'next/link';
import Ornament from './Ornament';

interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  href?: string;
  linkLabel?: string;
  as?: 'h1' | 'h2';
  align?: 'center' | 'left';
}

export default function SectionHeading({ title, subtitle, href, linkLabel = 'View all', as: Tag = 'h2', align = 'center' }: SectionHeadingProps) {
  return (
    <div className={`mb-8 ${align === 'center' ? 'text-center' : ''}`}>
      <Tag className="font-serif text-3xl font-bold text-maroon sm:text-4xl">{title}</Tag>
      {subtitle && <p className="mx-auto mt-2 max-w-2xl text-gray-600">{subtitle}</p>}
      {align === 'center' && <Ornament className="mt-3" />}
      {href && (
        <Link href={href} className="mt-3 inline-block text-sm font-semibold text-saffron hover:underline">
          {linkLabel} →
        </Link>
      )}
    </div>
  );
}

/** Standard page shell used by inner public pages. */
export function PageShell({ title, subtitle, children, narrow }: { title: string; subtitle?: string; children: React.ReactNode; narrow?: boolean }) {
  return (
    <div className="bg-cream">
      <div className="bg-gradient-to-b from-maroon to-maroon-dark px-4 py-12 text-center text-white">
        <h1 className="font-serif text-3xl font-bold sm:text-4xl">{title}</h1>
        {subtitle && <p className="mx-auto mt-2 max-w-2xl text-sm text-amber-100 sm:text-base">{subtitle}</p>}
        <Ornament className="mt-4 text-saffron-light" />
      </div>
      <div className={`mx-auto px-4 py-10 sm:px-6 ${narrow ? 'max-w-3xl' : 'max-w-6xl'}`}>{children}</div>
    </div>
  );
}
