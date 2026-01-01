import PageContainer from '@/components/PageContainer'

export default function DailyPoojasPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Daily Poojas</h1>
      <p className="mt-4 text-gray-700">The temple offers simple daily poojas to honour the deity. Details are managed by the temple administration.</p>

      <p className="mt-6 text-sm text-gray-500">Details will be updated by temple administration.</p>

      <ul className="mt-6 space-y-4">
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Morning Abhishekam (Template)</h3>
          <p className="text-gray-600 mt-1">Brief description placeholder. Specifics and scheduling will be provided later.</p>
        </li>
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Midday Archana (Template)</h3>
          <p className="text-gray-600 mt-1">Brief description placeholder. Details will be posted by the temple team.</p>
        </li>
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Evening Aarti (Template)</h3>
          <p className="text-gray-600 mt-1">Brief description placeholder. Timings and booking info will be shared when available.</p>
        </li>
      </ul>
    </PageContainer>
  )
}
