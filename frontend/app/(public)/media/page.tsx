import PageContainer from '@/components/PageContainer'

export default function MediaPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Media & Updates</h1>
      <p className="mt-4 text-gray-700">Latest announcements, events, and gallery updates will appear here when available.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Announcements</h2>
        <p className="mt-2 text-gray-600">Content will be updated soon.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Events</h2>
        <p className="mt-2 text-gray-600">Content will be updated soon.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Gallery</h2>
        <p className="mt-2 text-gray-600">Content will be updated soon.</p>
      </section>
    </PageContainer>
  )
}
