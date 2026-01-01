import PageContainer from '@/components/PageContainer'

export default function HelpDeskPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Help Desk</h1>
      <p className="mt-4 text-gray-700">For assistance during visits and events, the help desk will provide guidance and support.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Assistance</h2>
        <p className="mt-2 text-gray-600">Staff and volunteers will be available during visiting hours to assist visitors.</p>
      </section>
    </PageContainer>
  )
}
