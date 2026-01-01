/**
 * Environment configuration utilities for Next.js frontend.
 * 
 * Provides type-safe access to environment variables and
 * environment-specific feature flags.
 */

export type Environment = 'development' | 'production' | 'test';

/**
 * Get the current environment.
 */
export function getEnvironment(): Environment {
    const env = process.env.NEXT_PUBLIC_ENV || process.env.NODE_ENV || 'development';
    return env as Environment;
}

/**
 * Check if running in development mode.
 */
export function isDevelopment(): boolean {
    return getEnvironment() === 'development';
}

/**
 * Check if running in production mode.
 */
export function isProduction(): boolean {
    return getEnvironment() === 'production';
}

/**
 * Get the API base URL.
 * 
 * In development: Uses NEXT_PUBLIC_API_BASE_URL or defaults to /api/v1
 * In production: Uses strict NEXT_PUBLIC_API_BASE_URL
 */
export function getApiBaseUrl(): string {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';

    if (isProduction() && !process.env.NEXT_PUBLIC_API_BASE_URL) {
        console.error('NEXT_PUBLIC_API_BASE_URL not set in production!');
    }

    return baseUrl;
}

/**
 * Get the internal API base URL (for server-side requests).
 */
export function getInternalApiBaseUrl(): string {
    return process.env.INTERNAL_API_BASE_URL || 'http://backend:8000/api/v1';
}

/**
 * Feature flags based on environment.
 */
export const featureFlags = {
    /**
     * Show debug banner in development.
     */
    showDebugBanner: process.env.NEXT_PUBLIC_ENABLE_DEBUG_BANNER === 'true' || isDevelopment(),

    /**
     * Enable API request/response logging.
     */
    enableApiLogging: process.env.NEXT_PUBLIC_ENABLE_API_LOGGING === 'true' || isDevelopment(),

    /**
     * Show detailed error messages.
     */
    showDetailedErrors: isDevelopment(),

    /**
     * Enable mock data fallbacks.
     */
    enableMockFallbacks: isDevelopment(),
};

/**
 * Log environment information (development only).
 */
export function logEnvironmentInfo(): void {
    if (!isDevelopment()) return;

    console.log('='.repeat(60));
    console.log('🚀 Temple Management Frontend - DEVELOPMENT MODE');
    console.log('='.repeat(60));
    console.log('Environment:', getEnvironment());
    console.log('API Base URL:', getApiBaseUrl());
    console.log('Internal API URL:', getInternalApiBaseUrl());
    console.log('Feature Flags:', featureFlags);
    console.log('='.repeat(60));
}
