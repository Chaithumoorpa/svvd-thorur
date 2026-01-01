import PageContainer from '@/components/PageContainer'

export default function HistoryPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">History</h1>
      <p className="mt-4 text-gray-700">The temple's story is woven with local devotion and simple acts of service that have sustained it through generations.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Origins</h2>
        <p className="mt-2 text-gray-600">The exact origins are preserved in local memory; the shrine has long been a place for quiet worship and community gatherings.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Local Significance</h2>
        <p className="mt-2 text-gray-600">The temple plays a modest but meaningful role in village life, marking festivals and rites with humility and care.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Preservation</h2>
        <p className="mt-2 text-gray-600">Community stewardship ensures the temple remains a place of worship and cultural continuity.</p>
      </section>
    </PageContainer>
  )
}
