import React from 'react';

export default function HistoryPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-12">
            <h1 className="text-4xl font-bold text-templeDark mb-8">Temple History</h1>
            <div className="prose prose-lg">
                <p>
                    The origins of Sri Varasiddhi Vinayaka Swamy Temple date back several decades.
                    The temple was established with the vision of providing a dedicated space for the
                    community to offer prayers and seek blessings from Lord Ganesha.
                </p>
                <p>
                    Over the years, the temple has undergone significant renovations and enhancements,
                    expanding its facilities to accommodate the growing number of devotees.
                </p>
                <h2 className="text-2xl font-semibold mt-8 mb-4">Significant Milestones</h2>
                <ul className="list-disc pl-6 space-y-2">
                    <li>Establishment of the primary sanctum</li>
                    <li>Inauguration of the Annadanam hall</li>
                    <li>Expansion of the temple prakaram</li>
                    <li>Formation of the Temple Trust for better management</li>
                </ul>
            </div>
        </div>
    );
}
