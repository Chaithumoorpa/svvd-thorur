'use client';

import { useTranslations } from 'next-intl';
import PageContainer from '@/components/PageContainer';
import { PrinterIcon } from 'lucide-react';

// Archival donor records - see the comment in ../archive/page.tsx.
const landDonors = [
    { name: 'శ్రీ మూర్ప మునిరత్నం, తోరూరు' },
    { name: 'శ్రీ బేతు పెద్ద కన్నయ్య, తోరూరు' },
    { name: 'శ్రీ మన్నేపల్లి చంద్రకళ, తోరూరు' },
    { name: 'శ్రీ జలకం వెంకటముని' },
    { name: 'శ్రీ బేతు దొరస్వామి నాయుడు & సన్స్' },
    { name: 'శ్రీ గాలి రాధాకృష్ణయ్య & సన్స్' }
];

const itemDonations = [
    { name: 'శ్రీ యన్. సురేష్, M/o చంద్రమ్మ, టి.టి.డి. తిరుపతి', item: 'మూలస్థాన విగ్రహం' },
    { name: 'శ్రీమతి గుణ, శ్రీ రామ్మూర్తి, తిరుపతి', item: 'ఉత్సవ విగ్రహం' },
    { name: 'శ్రీ బి. పెద్దకన్నయ్య, Ex. M.P.T.C., తోరూరు', item: 'కలశం' },
    { name: 'శ్రీ బి.జె. మురళి, తోరూరు', item: 'గొముఖం' },
    { name: 'శ్రీ డా॥ ఐ. లోకనాథం, శ్రీ సాయిరామ్ క్లినిక్, పుత్తూరు', item: 'వెండితీర్థం గిన్నె, స్పూన్' },
    { name: 'శ్రీ ఆర్. వెంకటపతి (బాబు) AP Police , తోరూరు', item: 'శరారి' },
    { name: 'శ్రీ బి. పార్వతమ్మ, తోరూరు', item: 'ఆధారపీఠం, మోటర్ సెట్, వాటర్ ట్యాంక్' },
    { name: 'శ్రీ ఎ. కృష్ణయ్య, Forest Dept. , తోరూరు', item: 'గర్భగుడి ద్వారమందిరమునకు కలప దాత' },
    { name: 'శ్రీ బి. దాము, తోరూరు', item: 'లైటింగ్ నేమ్ బోర్డు' },
    { name: 'శ్రీ జయప్రకాశ్ (చిట్టి) Ex. Z.P.T.C., పుత్తూరు', item: '1.5 చ.అ. గ్రైనేట్' },
    { name: 'శ్రీ మూర్ప బాలాజి, AP Police, పుత్తూరు', item: '1.5 చ.అ. గ్రైనేట్' },
    { name: 'శ్రీ జె. భారతి, గోవిందయ్య, తోరూరు', item: 'సేఫ్టీ గ్రిల్' },
    { name: 'శ్రీ కె. షణ్ముగం, S/o కీ.శే. కైలాసం, పైడిపల్లి', item: 'మెయిన్ గేట్' },
    { name: 'శ్రీ జె. జయవేలు JM.Eng. , చెన్నై', item: 'మండపము తూర్పు గ్రిల్' },
    { name: 'శ్రీ చిరుమామిళ్ల బాబునాయుడు H.M, తోరూరు', item: 'మండపము దక్షిణ గ్రిల్' },
    { name: 'శ్రీ యన్.జె. వివేకానందం Retd. (H.V.F), తిరుత్తణి', item: 'మండపము ఉత్తర గ్రిల్' },
    { name: 'శ్రీ ఎ. మునెమ్మ భాస్కర్, తిరుపతి', item: 'కానుకల హుండి' },
    { name: 'శ్రీ జె. శ్రీదేవి రామ్మూర్తి, తోరూరు', item: 'దీపస్థంభం' },
    { name: 'శ్రీ యన్. సునంద వెంకటేశ్, తోరూరు', item: 'దీపస్థంభం' },
    { name: 'శ్రీ బి. లలిత, నాగరాజు, తోరూరు', item: 'గంట' },
    { name: 'శ్రీ యన్. సుబ్రహ్మణ్యం, (N.S.M) తోరూరు', item: 'అర్ధ యూనిట్ జెల్లి' },
    { name: 'శ్రీ గోపి నాయుడు (Retd. RPF), పుత్తూరు', item: 'అర్ధ యూనిట్ జెల్లి' },
    { name: 'శ్రీ గోపి సర్పంచ్, తోరూరు', item: '5 బ్యాగుల సిమెంట్' },
    { name: 'శ్రీ కె. యం. ఏలుమలై రెడ్డి, కొండలచెరువు', item: 'ఇటుక రాళ్ళు 2000' },
    { name: 'శ్రీ సంతోష్ & గజేంద్ర, తోరూరు', item: 'ఇటుక రాళ్ళు 1000' },
    { name: 'శ్రీ మూర్ప రమేష్ & సన్స్', item: 'నీళ్ళ మోటర్' },
];

export default function OldDonors() {
    const t = useTranslations('donations.oldDonors');
    const handlePrint = () => {
        window.print();
    };

    return (
        <PageContainer>
            <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 bg-white print:p-0">
                <div className="flex justify-between items-center mb-6 print:hidden">
                    <h1 className="text-2xl font-serif font-bold text-gray-900">{t('heading')}</h1>
                    <button
                        onClick={handlePrint}
                        className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded transition"
                    >
                        <PrinterIcon size={18} />
                        <span>{t('downloadPdf')}</span>
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
                        {/* Sthala Dathalu */}
                        <section>
                            <div className="inline-block border-2 border-gray-800 px-6 py-1 mb-6">
                                <h2 className="text-xl font-bold">{t('landDonorsHeading')}</h2>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-2">
                                {landDonors.map((item, index) => (
                                    <div key={index} className="flex gap-4 border-b border-gray-100 py-1">
                                        <span className="font-bold w-6">{index + 1}.</span>
                                        <span>{item.name}</span>
                                    </div>
                                ))}
                            </div>
                        </section>

                        {/* Vastu Rupena */}
                        <section>
                            <div className="inline-block border-2 border-gray-800 px-6 py-1 mb-6">
                                <h2 className="text-xl font-bold">{t('itemDonorsHeading')}</h2>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full border-collapse">
                                    <thead>
                                        <tr className="border-b-2 border-gray-800">
                                            <th className="text-left py-3 px-2 font-bold w-12">{t('colSerial')}</th>
                                            <th className="text-left py-3 px-2 font-bold">{t('colDonor')}</th>
                                            <th className="text-right py-3 px-2 font-bold w-48">{t('colItem')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {itemDonations.map((item, index) => (
                                            <tr key={index} className="border-b border-gray-300">
                                                <td className="py-2 px-2 text-gray-800">{index + 1}</td>
                                                <td className="py-2 px-2 text-gray-800">{item.name}</td>
                                                <td className="py-2 px-2 text-right font-semibold text-gray-900">{item.item}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    </div>

                    <div className="mt-12 pt-8 border-t border-gray-400 text-center italic text-sm text-gray-600">
                        <p>{t('footnote')}</p>
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
