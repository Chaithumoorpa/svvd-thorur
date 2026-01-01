import PageContainer from '@/components/PageContainer'

export default function SpecialSevasPage() {
  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Special Sevas</h1>
      <p className="mt-4 text-gray-700">Special sevas are performed on request and during certain observances. Administration will update details and availability.</p>

      <p className="mt-6 text-sm text-gray-500">Details will be updated by temple administration.</p>

      <ul className="mt-6 space-y-4">
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Home Blessing (Template)</h3>
          <p className="text-gray-600 mt-1">Placeholder item. No pricing or ritual specifics are published here.</p>
        </li>
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Temple Homa (Template)</h3>
          <p className="text-gray-600 mt-1">Placeholder item. Administration will share details when ready.</p>
        </li>
        <li className="border rounded p-4 bg-white shadow-sm">
          <h3 className="font-semibold">Name Ceremony (Template)</h3>
          <p className="text-gray-600 mt-1">Placeholder item. Please await official information from temple staff.</p>
        </li>
      </ul>
    </PageContainer>
  )
}
