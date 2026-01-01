import React from 'react';

export default function OverviewPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-12">
            <h1 className="text-4xl font-bold text-templeDark mb-8">Temple Overview</h1>
            <div className="prose prose-lg">
                <p>
                    Sri Varasiddhi Vinayaka Swamy Temple is a sacred place of worship dedicated to Lord Ganesha.
                    Located in Thorur, it serves as a spiritual hub for devotees from all over the region.
                </p>
                <p>
                    The temple is known for its serene atmosphere and the divine presence of Lord Vinayaka,
                    who is believed to be the remover of obstacles and the bestower of success.
                </p>
                <h2 className="text-2xl font-semibold mt-8 mb-4">Our Mission</h2>
                <p>
                    To maintain the sanctity of the temple, provide a spiritual environment for devotees,
                    and engage in community welfare activities through the temple trust.
                </p>
            </div>
        </div>
    );
}
