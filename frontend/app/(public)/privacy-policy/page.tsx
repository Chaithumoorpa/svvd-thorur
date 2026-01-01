import React from 'react';
import { ShieldAlert, Lock, Eye } from 'lucide-react';

export default function PrivacyPolicyPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-16">
            <h1 className="text-4xl font-bold text-templeDark mb-8">Privacy Policy</h1>

            <div className="prose prose-lg text-gray-600 space-y-8">
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <ShieldAlert className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark mb-0">Introduction</h2>
                    </div>
                    <p>
                        Sri Varasiddhi Vinayaka Swamy Temple ("we", "our", or "us") is committed to protecting your privacy.
                        This Privacy Policy explains how we collect, use, and safeguard your information when you visit our
                        website and use our services, including online seva bookings and donations.
                    </p>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <Eye className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark mb-0">Information We Collect</h2>
                    </div>
                    <p>
                        We may collect personal information such as your name, mobile number, email address, and
                        transaction details when you register for sevas or make donations. We also collect non-personal
                        data like browser type and IP address for analytics purposes.
                    </p>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <Lock className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark mb-0">Data Security</h2>
                    </div>
                    <p>
                        We implement a variety of security measures to maintain the safety of your personal information.
                        Your transaction data is processed through secure gateways and is never stored on our servers.
                    </p>
                </section>
            </div>
        </div>
    );
}
