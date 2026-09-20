/** Injects schema.org JSON-LD. Content is produced by JSON.stringify of our own data, never raw HTML. */
export default function JsonLd({ data }: { data: Record<string, unknown> }) {
  // "<" is escaped so admin-entered text can never close the script tag.
  const json = JSON.stringify(data).replace(/</g, '\\u003c');
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: json }} />;
}
