import React from 'react';
import { Clock, Sun, Moon } from 'lucide-react';

export default function TimingsPage() {
    return (
        <div className="max-w-4xl mx-auto px-4 py-12">
            <h1 className="text-4xl font-bold text-templeDark mb-8">Temple Timings</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-templeGold/10 p-8 rounded-2xl border border-templeGold/20">
                    <div className="flex items-center gap-3 mb-4">
                        <Sun className="text-templeGold w-8 h-8" />
                        <h2 className="text-2xl font-bold text-templeDark">Morning Session</h2>
                    </div>
                    <p className="text-3xl font-bold text-templeDark mb-2">6:00 AM - 12:30 PM</p>
                    <ul className="text-gray-600 space-y-2">
                        <li>• Suprabhatam: 6:00 AM</li>
                        <li>• Abhishekam: 7:00 AM</li>
                        <li>• Morning Archana: 9:00 AM onwards</li>
                    </ul>
                </div>

                <div className="bg-slate-900 p-8 rounded-2xl text-white">
                    <div className="flex items-center gap-3 mb-4">
                        <Moon className="text-templeGold w-8 h-8" />
                        <h2 className="text-2xl font-bold">Evening Session</h2>
                    </div>
                    <p className="text-3xl font-bold text-templeGold mb-2">4:30 PM - 8:30 PM</p>
                    <ul className="text-slate-400 space-y-2">
                        <li>• Evening Archana: 4:30 PM</li>
                        <li>• Harathi: 7:30 PM</li>
                        <li>• Ekantha Seva: 8:15 PM</li>
                    </ul>
                </div>
            </div>

            <div className="mt-12 p-6 bg-white border border-gray-100 rounded-2xl shadow-sm">
                <h3 className="text-xl font-bold text-templeDark mb-4">Note for Devotees</h3>
                <p className="text-gray-600">
                    Timings may vary during special festivals, eclipses, and special occasions.
                    Please check the announcements section for any changes in the schedule.
                </p>
            </div>
        </div>
    );
}
