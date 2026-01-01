'use client';

import React from 'react';
import Link from 'next/link';
import { UserPlus, ShieldAlert, ArrowLeft } from 'lucide-react';

export default function SignUpPage() {
    return (
        <div className="min-h-[80vh] flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="bg-white rounded-[2.5rem] shadow-2xl shadow-templeDark/5 p-10 border border-gray-100 text-center">
                    <div className="inline-flex p-4 bg-orange-50 rounded-2xl text-orange-500 mb-6">
                        <ShieldAlert className="w-8 h-8" />
                    </div>

                    <h1 className="text-3xl font-bold text-templeDark mb-4">Registration Locked</h1>
                    <p className="text-gray-500 mb-8 leading-relaxed">
                        Public registration is currently disabled by the temple management.
                        Only authorized personnel can create new accounts.
                    </p>

                    <div className="bg-gray-50 p-6 rounded-2xl mb-8 text-left">
                        <h3 className="font-bold text-templeDark text-sm mb-3 uppercase tracking-widest">Why is this?</h3>
                        <ul className="text-sm text-gray-600 space-y-3">
                            <li className="flex gap-2">
                                <span className="text-orange-500 font-bold">•</span>
                                Security measures for temple administration
                            </li>
                            <li className="flex gap-2">
                                <span className="text-orange-500 font-bold">•</span>
                                Pre-authorized trustee access only
                            </li>
                            <li className="flex gap-2">
                                <span className="text-orange-500 font-bold">•</span>
                                Maintaining data integrity
                            </li>
                        </ul>
                    </div>

                    <div className="space-y-4">
                        <Link
                            href="/"
                            className="flex items-center justify-center gap-2 w-full py-4 bg-gray-100 text-gray-600 font-bold rounded-2xl hover:bg-gray-200 transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Back to Home
                        </Link>

                        <p className="text-xs text-gray-400 px-4">
                            If you are a temple member or trustee and need access, please contact the main administration office.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
