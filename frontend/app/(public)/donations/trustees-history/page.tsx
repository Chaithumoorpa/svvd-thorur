'use client';

import PageContainer from '@/components/PageContainer';
import { PrinterIcon } from 'lucide-react';

const trusteesData = {
    founders: [
        { name: 'శ్రీ మూర్ప పురుషోత్తం S/o పోలయ్య', role: 'Retd Police, తోరూరు' }
    ],
    otherRoles: [
        { label: 'ఆలయ ప్రారంభం (Temple Inauguration)', name: 'శ్రీ సి. సంజీవ కుమార్, పురోహితులు' },
        { label: 'నిత్యపూజ అర్చకులు (Daily Pooja Priest)', name: 'జంగం శ్రీ రామ్మూర్తి దేవర్' },
        { label: 'ఆలయ నిర్మాణ శిల్పి (Temple Architect)', name: 'శ్రీ తపతి ఆర్. రాజేంద్రన్, తిరుపతి' },
        { label: 'ముఖద్వార తయారీ (Entrance Gate Maker)', name: 'శ్రీ వెంకట్రాయ ఆచారి, తోరూరు' }
    ]
};

export default function TrusteesHistory() {
    const handlePrint = () => {
        window.print();
    };

    return (
        <PageContainer>
            <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 bg-white print:p-0">
                <div className="flex justify-between items-center mb-6 print:hidden">
                    <h1 className="text-2xl font-serif font-bold text-gray-900">History & Founders</h1>
                    <button
                        onClick={handlePrint}
                        className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded transition"
                    >
                        <PrinterIcon size={18} />
                        <span>Download as PDF</span>
                    </button>
                </div>

                <div className="border-4 border-double border-gray-800 p-4 sm:p-8 font-serif bg-white text-gray-900">
                    <div className="text-center mb-10">
                        <h2 className="text-3xl font-bold mb-2">శ్రీ</h2>
                        <h1 className="text-3xl font-bold mb-4">శ్రీ వరసిద్ధి వినాయక స్వామి ఆలయం</h1>
                        <p className="text-lg font-medium">తోరూరు (గ్రామం), పుత్తూరు (మం)</p>
                        <p className="text-sm text-gray-600 mb-8">తిరుపతి జిల్లా, 517583. Regd No : 1026</p>
                    </div>

                    <div className="space-y-12">
                        {/* Founders */}
                        <section className="text-center">
                            <div className="inline-block border-2 border-gray-800 px-8 py-1 mb-6">
                                <h2 className="text-xl font-bold">ఆలయ వ్యవస్థాపకులు (Temple Founder)</h2>
                            </div>
                            {trusteesData.founders.map((item, index) => (
                                <div key={index} className="py-2">
                                    <p className="text-2xl font-bold text-gray-900">{item.name}</p>
                                    <p className="text-lg text-gray-700">{item.role}</p>
                                </div>
                            ))}
                        </section>

                        {/* Other Roles */}
                        <section className="grid grid-cols-1 gap-10">
                            {trusteesData.otherRoles.map((item, index) => (
                                <div key={index} className="text-center">
                                    <div className="inline-block border shadow-sm px-6 py-1 mb-3 bg-gray-50">
                                        <h3 className="text-lg font-bold">{item.label}</h3>
                                    </div>
                                    <p className="text-xl font-semibold text-gray-900">{item.name}</p>
                                </div>
                            ))}
                        </section>
                    </div>

                    <div className="mt-16 pt-8 border-t border-gray-400 text-center italic text-sm text-gray-600">
                        <p>"ఈ పేజీలో ఉన్న సమాచారం చారిత్రక రికార్డుల ఆధారంగా పొందుపరచబడింది. ఇది సమాచార ప్రయోజనాల కొరకు మాత్రమే."</p>
                    </div>
                </div>
            </div>

            <style jsx global>{`
        @media print {
          body * {
            visibility: hidden;
          }
          .print\:p-0, .print\:p-0 * {
            visibility: visible;
          }
          .print\:p-0 {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
          .print\:hidden {
            display: none !important;
          }
        }
      `}</style>
        </PageContainer>
    );
}
