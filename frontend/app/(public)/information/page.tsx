import React from 'react';
import { ShieldCheck, Info, UserCheck } from 'lucide-react';

export default function InformationPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-12">
            <h1 className="text-4xl font-bold text-templeDark mb-8">General Information</h1>

            <div className="space-y-12">
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <UserCheck className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark">Dress Code</h2>
                    </div>
                    <p className="text-gray-600 mb-4">
                        Devotees are requested to wear traditional Indian attire when visiting the temple.
                        Modest clothing that respects the sanctity of the temple is mandatory.
                    </p>
                    <ul className="grid grid-cols-2 gap-4">
                        <li className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span className="font-bold block mb-1">Men</span>
                            Dhoti, Kurta or Formal Clothing
                        </li>
                        <li className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span className="font-bold block mb-1">Women</span>
                            Saree, Chudidhar or Traditional Wear
                        </li>
                    </ul>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <ShieldCheck className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark">Rules & Regulations</h2>
                    </div>
                    <ul className="space-y-4">
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            Photography and videography inside the sanctum are strictly prohibited.
                        </li>
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            Please switch off or keep mobile phones in silent mode.
                        </li>
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            Devotees are requested to maintain silence and discipline inside the temple premises.
                        </li>
                        <li className="flex gap-3 text-gray-600">
                            <span className="text-templeGold font-bold">•</span>
                            Outside food and beverages are not allowed inside the temple.
                        </li>
                    </ul>
                </section>

                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <Info className="text-templeGold w-6 h-6" />
                        <h2 className="text-2xl font-bold text-templeDark">Facilities</h2>
                    </div>
                    <p className="text-gray-600">
                        The temple provides facilities such as safe drinking water, clean restrooms,
                        and a dedicated area for pilgrims to rest. Special assistance is available
                        for elderly and physically challenged devotees.
                    </p>
                </section>
            </div>
        </div>
    );
}
