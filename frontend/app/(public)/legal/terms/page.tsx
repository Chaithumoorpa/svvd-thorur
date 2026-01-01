import PageContainer from '@/components/PageContainer'

export default function TermsPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Terms & Conditions</h1>
      <p className="mt-4 text-gray-700">This is placeholder legal text for terms and conditions. The final document will be prepared by the temple trustees.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Use of Site</h2>
        <p className="mt-2 text-gray-600">Placeholder: acceptable use and limitations.</p>
      </section>

      <p className="mt-8 text-sm text-gray-500">Last updated: 2025-12-27</p>
    </PageContainer>
  )
}
