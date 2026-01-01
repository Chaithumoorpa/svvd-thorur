'use client';

import { featureFlags, getEnvironment, getApiBaseUrl } from '@/lib/env';

/**
 * Development mode banner component.
 * 
 * Shows a prominent banner at the top of the page in development mode
 * with quick links to API docs and environment information.
 */
export default function DevBanner() {
    // Only show in development
    if (!featureFlags.showDebugBanner) {
        return null;
    }

    const environment = getEnvironment();
    const apiBaseUrl = getApiBaseUrl();

    return (
        <div className="bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400 text-white px-4 py-2 shadow-lg">
            <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-3">
                    <span className="text-lg font-bold">🚧 DEV MODE</span>
                    <span className="text-sm opacity-90">
                        Environment: <strong>{environment}</strong>
                    </span>
                    <span className="text-sm opacity-90">
                        API: <strong>{apiBaseUrl}</strong>
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <a
                        href="/api/v1/docs"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs bg-white text-orange-600 px-3 py-1 rounded-full font-semibold hover:bg-orange-50 transition-colors"
                    >
                        📚 API Docs
                    </a>
                    <a
                        href="/api/v1/redoc"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs bg-white text-orange-600 px-3 py-1 rounded-full font-semibold hover:bg-orange-50 transition-colors"
                    >
                        📖 ReDoc
                    </a>
                    <button
                        onClick={() => {
                            console.log('Environment Info:', {
                                environment,
                                apiBaseUrl,
                                featureFlags,
                                timestamp: new Date().toISOString(),
                            });
                        }}
                        className="text-xs bg-white text-orange-600 px-3 py-1 rounded-full font-semibold hover:bg-orange-50 transition-colors"
                    >
                        🔍 Log Info
                    </button>
                </div>
            </div>
        </div>
    );
}
