import PageContainer from '@/components/PageContainer'

export default function TimingsPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Temple Timings</h1>
      <p className="mt-4 text-gray-700">Daily worship follows a rhythm of morning and evening prayers to welcome devotees throughout the day.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Morning</h2>
        <p className="mt-2 text-gray-600">Placeholder: Morning rituals and darshan times will be listed here.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Evening</h2>
        <p className="mt-2 text-gray-600">Placeholder: Evening aarti and closing times will be listed here.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Special Days</h2>
        <p className="mt-2 text-gray-600">Placeholder: Timings for festival days and special observances.</p>
      </section>
    </PageContainer>
  )
}
