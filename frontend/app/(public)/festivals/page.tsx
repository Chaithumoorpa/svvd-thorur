import { getFestivals } from '@/lib/api'

export const dynamic = 'force-dynamic'

type Festival = {
  id: number
  name: string
  date?: string
  description?: string
}

export default async function FestivalsPage() {
  let festivals: Festival[] = []
  try {
    festivals = await getFestivals()
  } catch (e) {
    console.error('Failed to fetch festivals', e)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Festivals</h1>
      <div className="space-y-4">
        {festivals.map((f) => (
          <div key={f.id} className="border rounded-lg p-4 bg-white shadow-sm">
            <h3 className="font-semibold">{f.name}</h3>
            <p className="text-sm text-gray-600">{f.date}</p>
            <p className="mt-2 text-gray-700">{f.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
