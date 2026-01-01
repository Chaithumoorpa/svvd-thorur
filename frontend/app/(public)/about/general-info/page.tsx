import PageContainer from '@/components/PageContainer'

export default function GeneralInfoPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">General Information</h1>
      <p className="mt-4 text-gray-700">Basic visitor guidelines and helpful notes to make your visit respectful and comfortable.</p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Dress Code</h2>
        <p className="mt-2 text-gray-600">Visitors are requested to dress modestly. Traditional attire is welcomed but not mandatory.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Silence & Conduct</h2>
        <p className="mt-2 text-gray-600">Maintain a peaceful demeanour inside the sanctum and surrounding areas; avoid loud conversations.</p>
      </section>

      <section className="mt-6">
        <h2 className="text-xl font-semibold">Cleanliness</h2>
        <p className="mt-2 text-gray-600">Please keep the premises clean; use designated areas for offerings and dispose of litter responsibly.</p>
      </section>
    </PageContainer>
  )
}
