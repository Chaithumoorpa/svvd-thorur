import React from 'react';
import { FileText, Gavel, AlertCircle } from 'lucide-react';

export default function TermsPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-16">
            <h1 className="text-4xl font-bold text-templeDark mb-8">Terms & Conditions</h1>

            <div className="prose prose-lg text-gray-600 space-y-8">
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <FileText className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark mb-0">1. Acceptance of Terms</h2>
                    </div>
                    <p>
                        By accessing and using this website, you agree to comply with and be bound by these Terms and
                        Conditions. If you do not agree to these terms, please refrain from using our services.
                    </p>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <AlertCircle className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark mb-0">2. Seva Bookings & Donations</h2>
                    </div>
                    <p>
                        All seva bookings and donations are final. No refunds will be processed unless there is a
                        duplicate transaction or a technical error on our part. Devotees must present their digital
                        or printed ticket at the temple counter for verification.
                    </p>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <Gavel className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark mb-0">3. Code of Conduct</h2>
                    </div>
                    <p>
                        Devotees are expected to follow the temple rules, dress code, and maintain discipline. The
                        temple management reserves the right to deny entry to anyone violating the rules or
                        disturbing the sanctity of the temple.
                    </p>
                </section>
            </div>
        </div>
    );
}
