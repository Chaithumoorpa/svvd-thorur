import PageContainer from '@/components/PageContainer'

export default function OverviewPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">About the Temple — Overview</h1>
      <p className="mt-4 text-gray-700">Sri Varasiddhi Vinayaka Swamy Temple stands as a quiet centre of devotion and community life. Visitors are welcomed with simple, reverent hospitality.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Temple Intro</h2>
        <p className="mt-2 text-gray-600">A serene shrine dedicated to Vinayaka where daily worship and simple rituals keep the spirit of devotion alive.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Location</h2>
        <p className="mt-2 text-gray-600">Located in Thorur village, the temple is easily accessible by local roads and welcomes pilgrims and visitors alike.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Visiting</h2>
        <p className="mt-2 text-gray-600">Visitors are encouraged to come with a calm heart and respectful attire. Please follow on-site signs and guidance from volunteers.</p>
      </section>
    </PageContainer>
  )
}
