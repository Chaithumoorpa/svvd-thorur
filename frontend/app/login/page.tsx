"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { LogIn, Eye, EyeOff } from 'lucide-react';
import { api } from '@/lib/api';

export default function LoginPage() {
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

      // Store token in localStorage
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);

        if (data.must_change_password) {
          localStorage.setItem('must_change_password', 'true');
          window.location.href = '/admin/change-password';
        } else {
          localStorage.removeItem('must_change_password');
          // Use window.location for a full page reload to ensure auth state is fresh
          window.location.href = '/admin';
        }
      }
    } catch (err: any) {
      console.error('Login error:', err);

      // Normalize API error detail into a string so React doesn't attempt
      // to render an object (which causes "Objects are not valid as a React child").
      const responseData = err?.response?.data;
      let msg = 'Login failed. Please try again.';

      if (responseData?.detail) {
        const detail = responseData.detail;
        if (Array.isArray(detail)) {
          msg = detail
            .map((d) => {
              if (typeof d === 'string') return d;
              return (d && (d.msg || JSON.stringify(d))) || JSON.stringify(d);
            })
            .join('; ');
        } else if (typeof detail === 'string') {
          msg = detail;
        } else if (typeof detail === 'object') {
          msg = detail.msg || JSON.stringify(detail);
        }
      } else if (responseData?.message) {
        msg = responseData.message;
      } else if (err?.message) {
        msg = err.message;
      }

      setError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-lg shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="p-3 bg-slate-900 rounded-lg">
                <LogIn className="w-6 h-6 text-white" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Temple Admin</h1>
            <p className="text-gray-600 text-sm mt-1">Sign in to your account</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none transition-all"
                placeholder="admin"
                disabled={isLoading}
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none transition-all"
                  placeholder="••••••••"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                  disabled={isLoading}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-6 px-4 py-2 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center text-sm text-gray-600">
            <p>
              Back to{' '}
              <Link href="/" className="text-slate-900 hover:underline font-medium">
                Home
              </Link>
            </p>
          </div>
        </div>

        {/* Info Text */}
        <div className="mt-6 text-center text-gray-300 text-xs">
          <p>Demo: Use admin credentials provided during setup</p>
        </div>
      </div>
    </div>
  );
}
