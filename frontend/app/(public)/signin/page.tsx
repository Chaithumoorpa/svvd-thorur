'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { LogIn, Eye, EyeOff, Lock, User as UserIcon } from 'lucide-react';
import { api } from '@/lib/api';

export default function SignInPage() {
    const router = useRouter();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const response = await api.post('/auth/login', {
                username,
                password,
            });

            const data = response.data;

            if (data.access_token) {
                localStorage.setItem('token', data.access_token);

                // Verify token to get roles
                const verifyRes = await api.get('/auth/verify');
                const userInfo = verifyRes.data;

                // Role-aware redirection
                if (userInfo.is_admin || userInfo.is_super_admin || userInfo.is_trustee) {
                    window.location.href = '/admin';
                } else {
                    window.location.href = '/profile'; // General users (though none yet)
                }
            }
        } catch (err: any) {
            console.error('Login error:', err);
            setError('Invalid username or password. Please try again.');
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-[80vh] flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="bg-white rounded-[2.5rem] shadow-2xl shadow-templeDark/5 p-10 border border-gray-100">
                    <div className="text-center mb-10">
                        <div className="inline-flex p-4 bg-templeGold/10 rounded-2xl text-templeGold mb-6">
                            <Lock className="w-8 h-8" />
                        </div>
                        <h1 className="text-3xl font-bold text-templeDark">Welcome Back</h1>
                        <p className="text-gray-500 mt-2">Sign in to access the temple portal</p>
                    </div>

                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm font-medium">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-bold text-templeDark mb-2 ml-1">Username</label>
                            <div className="relative">
                                <UserIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    className="w-full pl-12 pr-4 py-3.5 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-templeGold/20 focus:border-templeGold outline-none transition-all placeholder:text-gray-400"
                                    placeholder="Enter your username"
                                    disabled={isLoading}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-templeDark mb-2 ml-1">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full pl-12 pr-12 py-3.5 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-templeGold/20 focus:border-templeGold outline-none transition-all placeholder:text-gray-400"
                                    placeholder="••••••••"
                                    disabled={isLoading}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-templeGold transition-colors"
                                    disabled={isLoading}
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        <div className="flex items-center justify-between text-sm px-1 pt-1">
                            <label className="flex items-center gap-2 text-gray-500 cursor-pointer">
                                <input type="checkbox" className="rounded border-gray-300 text-templeGold focus:ring-templeGold" />
                                Remember me
                            </label>
                            <Link href="/forgot-password" title="Coming Soon" className="text-templeGold font-bold hover:underline">
                                Forgot Password?
                            </Link>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full mt-4 py-4 bg-templeDark text-templeGold font-black rounded-2xl shadow-lg shadow-templeDark/10 hover:bg-slate-800 transition-all transform active:scale-[0.98] disabled:opacity-50"
                        >
                            {isLoading ? 'Processing...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="mt-8 text-center text-sm text-gray-500">
                        <p>
                            Don't have an account?{' '}
                            <Link href="/signup" className="text-templeDark font-bold hover:text-templeGold transition-colors">
                                Sign Up
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
