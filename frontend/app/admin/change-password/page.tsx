"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

export default function ChangePasswordPage() {
    const router = useRouter();
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (newPassword !== confirmPassword) {
            setError('New passwords do not match');
            return;
        }

        if (newPassword.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }

        setIsLoading(true);
        try {
            await api.post('/auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword,
            });

            localStorage.removeItem('must_change_password');
            setSuccess(true);

            // Redirect after 2 seconds
            setTimeout(() => {
                window.location.href = '/admin';
            }, 2000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to change password');
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-200px)] flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md border border-slate-100">
                <div className="text-center mb-8">
                    <div className="inline-flex p-3 bg-slate-900 rounded-lg mb-4">
                        <Lock className="w-6 h-6 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">Change Password</h1>
                    <p className="text-gray-500 mt-2">
                        {success ? 'Success! Redirecting you...' : 'For security, please set a new password for your account.'}
                    </p>
                </div>

                {success ? (
                    <div className="flex flex-col items-center py-6">
                        <CheckCircle className="w-16 h-16 text-green-500 mb-4 animate-bounce" />
                        <p className="text-green-600 font-medium">Password changed successfully!</p>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                                <p className="text-red-700 text-sm">{error}</p>
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Current Password
                            </label>
                            <input
                                type="password"
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)}
                                className="w-full px-4 py-2 border border-brand-light rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                New Password
                            </label>
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="w-full px-4 py-2 border border-brand-light rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none"
                                required
                                disabled={isLoading}
                                placeholder="Min 8 characters"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Confirm New Password
                            </label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="w-full px-4 py-2 border border-brand-light rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent outline-none"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-all disabled:opacity-50 mt-4 shadow-md active:scale-[0.98]"
                        >
                            {isLoading ? 'Processing...' : 'Update Password'}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}
