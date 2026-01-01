import PageContainer from '@/components/PageContainer'

export default function FestivalSevasPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Festival Sevas</h1>
      <p className="mt-4 text-gray-700">During festivals, special sevas may be organised to mark the occasion. Please check back for official announcements.</p>

      <p className="mt-6 text-sm text-gray-500">Details will be updated by temple administration.</p>

      <ul className="mt-6 space-y-4">
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Festival Pooja (Template)</h3>
          <p className="text-gray-600 mt-1">Placeholder item for festival-related sevas. Final details will be posted by the temple.</p>
        </li>
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Annadanam (Template)</h3>
          <p className="text-gray-600 mt-1">Placeholder item. No prices or schedules are published here.</p>
        </li>
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Procession (Template)</h3>
          <p className="text-gray-600 mt-1">Placeholder item. Event logistics will be communicated via official channels.</p>
        </li>
      </ul>
    </PageContainer>
  )
}
