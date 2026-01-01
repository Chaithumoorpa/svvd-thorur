import PageContainer from '@/components/PageContainer'

export default function FeedbackPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Feedback</h1>
      <p className="mt-4 text-gray-700">We welcome your feedback. A simple feedback form will be provided soon.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Note</h2>
        <p className="mt-2 text-gray-600">Feedback submission will be enabled by the temple administration.</p>
      </section>
    </PageContainer>
  )
}
