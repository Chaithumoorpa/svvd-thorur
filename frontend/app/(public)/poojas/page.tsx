import { getPoojas } from '@/lib/api'

export const dynamic = 'force-dynamic'

type Pooja = {
  id: number
  name: string
  start_time?: string
  end_time?: string
  is_paid?: boolean
  suggested_amount?: number | null
}

export default async function PoojasPage() {
  let poojas: Pooja[] = []
  try {
    poojas = await getPoojas()
  } catch (e) {
    console.error('Failed to fetch poojas', e)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Poojas</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {poojas.map((p) => (
          <div key={p.id} className="border rounded-lg p-4 bg-white shadow-sm">
            <h3 className="font-semibold">{p.name}</h3>
            <p className="text-sm text-gray-600">{p.start_time || '—'} → {p.end_time || '—'}</p>
            <div className="mt-2">
              {p.is_paid ? (
                <span className="inline-block bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Paid</span>
              ) : (
                <span className="inline-block bg-green-100 text-green-800 px-2 py-1 rounded">Free</span>
              )}
            </div>
            {p.suggested_amount ? <p className="text-sm text-gray-700 mt-2">Suggested: ₹{p.suggested_amount}</p> : null}
          </div>
        ))}
      </div>
    </div>
  )
}
