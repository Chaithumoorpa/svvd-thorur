import PageContainer from '@/components/PageContainer'
import Link from 'next/link'

export default function DonationsComingSoon() {
  return (
    <PageContainer>
      <h1 className="text-4xl font-serif font-semibold text-templeDark">Donations — Coming Soon</h1>
      <p className="mt-4 text-gray-700">We are preparing a transparent and devotional donations experience. Your contributions will be handled with care and clear accounting.</p>

      <div className="mb-12">
        <h2 className="text-2xl font-serif font-semibold text-templeDark mb-6">Historical Donation Records (ధనరాశి విరాళాలు)</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link href="/donations/archive" className="block p-6 border rounded-lg hover:shadow-md transition bg-white group border-templeGold/20">
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-templeGold transition font-serif">ధనరాశి విరాళాలు</h3>
            <p className="text-sm text-gray-500 mt-2">Historical Monetary Records</p>
          </Link>
          <Link href="/donations/old-donors" className="block p-6 border rounded-lg hover:shadow-md transition bg-white group border-templeGold/20">
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-templeGold transition font-serif">వస్తు & స్థల దాతలు</h3>
            <p className="text-sm text-gray-500 mt-2">Land & Item Donors (Archive)</p>
          </Link>
          <Link href="/donations/trustees-history" className="block p-6 border rounded-lg hover:shadow-md transition bg-white group border-templeGold/20">
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-templeGold transition font-serif">పూర్వ పాలక మండలి</h3>
            <p className="text-sm text-gray-500 mt-2">Historical Committee & Founders</p>
          </Link>
        </div>
        <p className="mt-8 italic text-sm text-gray-500 text-center">
          "ఈ సమాచారం చారిత్రక రికార్డుల ఆధారంగా పొందుపరచబడింది."
        </p>
      </div>

      <div className="mt-8 border rounded p-6 bg-gray-50 shadow-inner text-center">
        <p className="text-2xl font-semibold text-gray-700">Online Donations Coming Soon</p>
        <p className="mt-3 text-gray-500">Donation forms and payment options will be enabled soon by the temple administration.</p>
        <div className="mt-6 flex justify-center gap-4">
          <button className="bg-white border text-gray-400 px-6 py-2 rounded font-semibold cursor-not-allowed" disabled>
            Donate (Disabled)
          </button>
        </div>
      </div>
    </PageContainer>
  )
}
