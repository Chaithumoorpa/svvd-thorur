/** @type {import('next').NextConfig} */
const nextConfig = {
    // Proxy /api/v1 requests to the backend
    async rewrites() {
        const backendUrl = process.env.INTERNAL_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
        return [
            {
                source: '/api/v1/:path*',
                destination: `${backendUrl}/:path*`,
            },
        ];
    },

    // Disable strict mode for compatibility
    reactStrictMode: false,

    // Type errors fail the build (the codebase type-checks clean with `tsc --noEmit`).
    // ESLint stays off during builds: there is no ESLint config in this project.
    eslint: {
        ignoreDuringBuilds: true,
    },

    // Output configuration for Docker
    output: 'standalone',
};

export default nextConfig;
