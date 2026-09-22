'use client';

import { useTranslations } from 'next-intl';
import PageContainer from '@/components/PageContainer';
import { PrinterIcon } from 'lucide-react';

// Historical donor records, transcribed verbatim from the temple's paper ledgers.
// This is archival content, not UI copy - it stays in its original Telugu across
// every locale (the temple's own convention for these records), same as the
// section headings below drawn from the same ledgers.
const archiveData = [
    // Data from Image 4
    { name: 'శ్రీ మూర్ప హరికళ పురుషోత్తం Retd., Police, తోరూరు', amount: '1,00,999' },
    { name: 'శ్రీ మూర్ప హరిప్రసాద్ (బాబు), తోరూరు', amount: '40,000' },
    { name: 'శ్రీ మూర్ప మునిరత్నం మరియు హేమకుమార్, తోరూరు', amount: '25,000' },
    { name: 'శ్రీ యం. రామలింగం & పార్థసారథి, తోరూరు', amount: '15,116' },
    { name: 'శ్రీ యన్. సురేష్, Prop. Veena Fast Food, Renigunta', amount: '15,116' },
    { name: 'శ్రీ జె. మురళి, S/o కీ.శే. వెంకటముని, తోరూరు', amount: '10,000' },
    { name: 'శ్రీ బి. మునిరాజు చీటి మొంబర్లు, తోరూరు', amount: '10,000' },
    { name: 'శ్రీ రైతు సంఘం, మరియు బాలాజి చిట్ మొంబర్లు, తోరూరు', amount: '7,800' },
    { name: 'శ్రీ వి. దీనదయాల్, ISHRO Tech., Sulurpet', amount: '5,116' },
    { name: 'శ్రీ బి. చంద్ర ఓబుల రెడ్డి, Contractor, Mudhanur', amount: '5,116' },
    { name: 'శ్రీ జె. మల్లికార్జున నాయుడు, M.G.M. Schools, శ్రీకాళహస్తి', amount: '5,000' },
    { name: 'శ్రీ యన్.ఆర్. వెంకటేశన్ (స్వామి), గుంతకల్', amount: '5,000' },
    { name: 'శ్రీ బి. శ్రీనివాసులు, S/o కీ.శే. దొరస్వామి నాయుడు, తోరూరు', amount: '5,000' },
    { name: 'వసూల చేయించిన దాత: కీ.శే. బి. రమేష్ బాబు A.P. Police,, తోరూరు', amount: '4,009' },
    { name: 'శ్రీ శాంతిలాల్ జైన్, నెల్లూరు', amount: '3,016' },
    { name: 'శ్రీ పి.యన్. రాజారాం, సేలం', amount: '2,500' },
    { name: 'యర్రగుంట్ల వెండి వ్యాపారస్తులు', amount: '2,500' },
    { name: 'శ్రీ వేములయ్య, సెక్యూరిటీ ఆఫీసర్, ఆటోనగర్', amount: '2,300' },
    { name: 'జీప్ డ్రైవర్స్ & ఓనర్స్, హరి ద్వారా వసూలు రేణిగుంట', amount: '2,200' },
    { name: 'శ్రీ యం.సి. సుబ్రహ్మణ్యం, APSRTC పుత్తూరు', amount: '2,116' },
    { name: 'శ్రీ జె. సుబ్రహ్మణ్యం నాయుడు, CRPF కూసమరాజుపాలెo', amount: '2,116' },
    { name: 'శ్రీ శంకరయ్య, టి.టి.డి. తిరుపతి', amount: '2,116' },
    { name: 'శ్రీమతి & శ్రీ రమాదేవి, మురళి, సూలూరు పేట', amount: '2,116' },
    { name: 'శ్రీ పి. ప్రభాకర్, A.P. Police శ్రీకాళహస్తి', amount: '2,116' },
    { name: 'శ్రీ వి. గిరిధర్ నాయర్, P.F. Stall రేణిగుంట', amount: '1,617' },
    { name: 'శ్రీ యస్. మునిరాజు, తోరూరు', amount: '1,516' },
    { name: 'శ్రీ మూర్ప నాగరాజు, Irrigation Dept. తిరుపతి', amount: '1,516' },
    { name: 'శ్రీ బి. నటరాజు, కొండలచెరువు', amount: '1,500' },
    { name: 'వసూల చేయించిన దాత: జె. సుబ్రహ్మణ్యం, CONDUCTOR,, తోరూరు', amount: '1,423' },
    { name: 'శ్రీ జె. నవనీత శేఖర్, పుత్తూరు', amount: '1,116' },
    { name: 'శ్రీ వెంకటేశ్, మయూరి సిల్వర్ ప్యాలస్, నెల్లూరు', amount: '1,116' },
    { name: 'శ్రీ జె. పురుశోత్తం, APSRTC తోరూరు', amount: '1,116' },
    { name: 'శ్రీ యం. కమలనాథుడు, ఉజ్జినాయుడు కండ్రిగ', amount: '1,116' },
    { name: 'శ్రీ బి. మునికృష్ణ, S/o రామయ్య, తోరూరు', amount: '1,116' },
    { name: 'శ్రీ బి. బాలబొజ్జన్న, అనంతపురం', amount: '1,116' },
    { name: 'శ్రీ బి.ఎ. కేశవ మేస్త్రీ, పుత్తూరు', amount: '1,116' },

    // Data from Image 1
    { name: 'శ్రీ పి. జయచంద్ర, S/o గోవిందయ్య, తోరూరు', amount: '1,116' },
    { name: 'శ్రీ డి. నరేష్ బాబు, APSRTC తోరూరు', amount: '1,116' },
    { name: 'శ్రీ యం. వాసు, APSRTC తోరూరు', amount: '1,116' },
    { name: 'శ్రీ యం. కన్నయ్య TTD తిరుపతి', amount: '1,116' },
    { name: 'శ్రీ పి. రామకృష్ణ, A.D. (JENCO) పుత్తూరు', amount: '1,116' },
    { name: 'శ్రీ డా॥ యస్. ప్రకాశ్ రాజ్, రాచపాలెం', amount: '1,116' },
    { name: 'శ్రీమతి టి. ప్రమీళ, Teacher తోరూరు', amount: '1,116' },
    { name: 'శ్రీ జె. నరేంద్ర బాబు, తిరుపతి', amount: '1,116' },
    { name: 'శ్రీ కె.పి. సిద్ధారెడ్డి, Retd. Police, తిరుపతి', amount: '1,116' },
    { name: 'శ్రీ ఎ. భాస్కర్, పండ్ల వ్యాపారం, తిరుపతి', amount: '1,116' },
    { name: 'శ్రీ యం.జి. కుప్పస్వామి A.P. Police, గూడూరు', amount: '1,116' },
    { name: 'శ్రీ కె.యం. నరసింహులు A.P. Police, తిరుపతి', amount: '1,116' },
    { name: 'శ్రీ కె.యం. శ్రీనివాసులు TTD, తిరుపతి', amount: '1,116' },
    { name: 'శ్రీ జె.ఆర్. రమేష్, బెంగుళూరు', amount: '1,116' },
    { name: 'శ్రీ డి. వెంకటపతి, తోరూరు', amount: '1,116' },
    { name: 'శ్రీ ఆర్. డాన్ ప్రకాష్, S/o కీ.శే. బొగ్గుల నాయుడు, పుత్తూరు', amount: '1,116' },
    { name: 'శ్రీ సి. శశికుమార్, చెన్నై', amount: '1,116' },
    { name: 'శ్రీ బి. సురేష్, కాట్పాడి', amount: '1,116' },
    { name: 'శ్రీ పి. సుబ్రహ్మణ్యం రెడ్డి (మునీంద్ర), తోరూరు', amount: '1,116' },
    { name: 'శ్రీ యస్.వి. నందకుమార్, పట్టాభిరామ్, చెన్నై', amount: '1,116' },
    { name: 'శ్రీ కె.వి. రమణ A.P. Police, తిరుపతి', amount: '1,100' },
    { name: 'శ్రీ బి. రఘుపతి Ex. Serviceman, పుత్తూరు', amount: '1,016' },
    { name: 'శ్రీ బి. నాగరాజు GBS Bus Owner', amount: '1,001' },
    { name: 'శ్రీ కీర్తి మ్యాచింగ్ సెంటర్, పుత్తూరు', amount: '1,001' },
    { name: 'శ్రీ యస్. లక్ష్మీపతి, DSJ, పుత్తూరు', amount: '1,001' },
    { name: 'శ్రీ సి. శంకరయ్య, Retd. Police, తిరుపతి', amount: '1,001' },
    { name: 'శ్రీ మూర్ప సొరకాయలు, తోరూరు', amount: '1,001' },
    { name: 'శ్రీ బి. కృష్ణయ్య, Ex. Sarpanch, తోరూరు', amount: '1,001' },
    { name: 'శ్రీ బి. చిన్న కన్నయ్య, తోరూరు', amount: '1,001' },
    { name: 'శ్రీ మూర్ప రమేష్, తోరూరు', amount: '1,001' },
    { name: 'శ్రీ యస్. సత్య, పుత్తూరు', amount: '1,001' },
    { name: 'శ్రీ వర్మరాజు, S.B.R.పురం', amount: '1,001' },
    { name: 'శ్రీ బి. బుజ్జి, తిరుపతి', amount: '1,000' },
    { name: 'శ్రీ కె. శరవణ, సేలం', amount: '1,000' },
    { name: 'శ్రీ డి. ముక్కుందరాజన్, కోయంబత్తూరు', amount: '1,000' },
    { name: 'శ్రీ యస్.కన్నయ్య, Retd. Police, తిరుపతి', amount: '1,000' },
    { name: 'శ్రీ జి. సెల్వం, సేలం', amount: '1,000' },

    // Data from Image 2
    { name: 'శ్రీ యం. నారాయణ, S.B.I. Zonal, తిరుపతి', amount: '1,000' },
    { name: 'శ్రీ బి. గుర్రప్ప, Retd. APSRTC, తోరూరు', amount: '1,000' },
    { name: 'శ్రీ వి. గోపాల్ ముందడి, గొల్లకండ్రిగ', amount: '632' },
    { name: 'శ్రీ జె. విజయకుమార్, Fire Service పుత్తూరు', amount: '516' },
    { name: 'శ్రీ డి. వెంకటముని, (ఎర్రబ్బ), తోరూరు', amount: '516' },
    { name: 'శ్రీ ఎ. వాసుదేవనాయుడు, Hotel రేణిగుంట', amount: '516' },
    { name: 'శ్రీ యం. నరసింహులు, A.P. Police, రేణిగుంట', amount: '516' },
    { name: 'శ్రీ టి. ప్రభాకర్, తోరూరు', amount: '516' },
    { name: 'శ్రీ ఎ. వీరాస్వామి, తిరుపతి', amount: '516' },
    { name: 'శ్రీ సి.హెచ్.పద్మనాభం, A.P. Police, రేణిగుంట', amount: '516' },
    { name: 'శ్రీ ఆర్. మధుసూధన్, పుత్తూరు', amount: '516' },
    { name: 'శ్రీ జె. రఘురామరాజు, రాజంపేట', amount: '516' },
    { name: 'శ్రీ సి.యం. దేశయ్య, చెన్నై', amount: '501' },
    { name: 'శ్రీ యం. విజయకుమార్, చెన్నై', amount: '501' },
    { name: 'శ్రీ జి. మోహన్ రాజు, గట్టు', amount: '501' },
    { name: 'శ్రీ కె. ప్రసాద్, Retd. Police, కడప', amount: '501' },
    { name: 'శ్రీ జె. నిమ్మమ్మ, తోరూరు', amount: '501' },
    { name: 'శ్రీ బి. భాస్కర్, తోరూరు', amount: '501' },
    { name: 'శ్రీ యం. సుబ్రహ్మణ్యం, APSRTC తోరూరు', amount: '501' },
    { name: 'శ్రీమతి బి. ఢిల్లీ రాణి, తోరూరు', amount: '501' },
    { name: 'శ్రీమతి భాగ్యలక్ష్మి ఫర్టిలైజర్స్, పుత్తూరు', amount: '501' },
    { name: 'శ్రీ సి. వెంకటయ్య రైస్ మిల్, కొండలచెరువు', amount: '501' },
    { name: 'శ్రీ వి. చంద్రబాబు, Retd, (S.B.I) పుత్తూరు', amount: '501' },
    { name: 'శ్రీ సి. వెంకటముని, తిరుచానూరు', amount: '501' },
    { name: 'శ్రీ పి. రంగయ్య, A.P. Police, తిరుపతి', amount: '501' },
    { name: 'శ్రీ జె. సుబ్రహ్మణ్యం, Vijaya Bank, తిరుత్తణి', amount: '501' },
    { name: 'శ్రీ జె. భాస్కర్, APSRTC, తోరూరు', amount: '501' },
    { name: 'శ్రీమతి జి. దొరసానమ్మ, తోరూరు', amount: '501' },
    { name: 'శ్రీ మురళికృష్ణ రెడ్డి, తిరుపతి', amount: '500' },
    { name: 'శ్రీ బి. గురుమూర్తి, తిరుపతి', amount: '500' },
    { name: 'శ్రీ కె. ముస్తఫా, రేణిగుంట', amount: '500' },
    { name: 'శ్రీ టి. సుబ్రహ్మణ్యం రెడ్డి, నేసనూరు', amount: '500' },
    { name: 'శ్రీ నటరాజ, పాలవ్యాపారి, పుత్తూరు', amount: '500' },
    { name: 'శ్రీ జి. రఘోత్తం, APSRTC, తోరూరు', amount: '500' },
    { name: 'శ్రీ జె. రామ్మూర్తి, APSRTC, తోరూరు', amount: '500' },
];

export default function DonationArchive() {
    const t = useTranslations('donations.archive');
    const handlePrint = () => {
        window.print();
    };

    return (
        <PageContainer>
            <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 bg-white print:p-0">
                {/* Print Header */}
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
                        <h1 className="text-4xl font-bold mb-4">ధనరాశి విరాళాలు (Historical Donation Records)</h1>
                        <h3 className="text-2xl font-bold mb-2">శ్రీ వరసిద్ధి వినాయక స్వామి ఆలయం</h3>
                        <p className="text-lg font-medium">తోరూరు (గ్రామం), పుత్తూరు (మం)</p>
                        <p className="text-sm text-gray-600">తిరుపతి జిల్లా, 517583. Regd No : 1026</p>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                            <thead>
                                <tr className="border-b-2 border-gray-800">
                                    <th className="text-left py-3 px-2 font-bold w-12">{t('colSerial')}</th>
                                    <th className="text-left py-3 px-2 font-bold">{t('colDonor')}</th>
                                    <th className="text-right py-3 px-2 font-bold w-40">{t('colAmount')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {archiveData.map((item, index) => (
                                    <tr key={index} className="border-b border-gray-300">
                                        <td className="py-2 px-2 text-gray-800">{index + 1}</td>
                                        <td className="py-2 px-2 text-gray-800">{item.name}</td>
                                        <td className="py-2 px-2 text-right font-semibold text-gray-900">{t('currencyPrefix')} {item.amount}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="mt-12 pt-8 border-t border-gray-400 text-center italic text-sm text-gray-600">
                        <p>{t('footnote1')}</p>
                        <p className="mt-4">{t('footnote2')}</p>
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
