import Header from '@/components/Header'
import Footer from '@/components/Footer'
import VisitorTracker from '@/components/VisitorTracker'

export default function PublicLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <>
            <VisitorTracker />
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
        </>
    )
}
