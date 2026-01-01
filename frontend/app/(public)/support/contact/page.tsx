import PageContainer from '@/components/PageContainer'

export default function ContactPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Contact</h1>
      <p className="mt-4 text-gray-700">For general enquiries and temple office hours, please use the contact details below.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Office</h2>
        <p className="mt-2 text-gray-600">Phone: +91-XXXXXXXXXX</p>
        <p className="mt-1 text-gray-600">Email: info@svvdthorur.org</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Visiting Hours</h2>
        <p className="mt-2 text-gray-600">Please check the timings page for daily darshan hours and special schedules.</p>
      </section>
    </PageContainer>
  )
}
