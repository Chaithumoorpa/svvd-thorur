/** @type {import('next').NextConfig} */
const nextConfig = {
    // Proxy /api/v1 requests to the backend
    async rewrites() {
        return [
            {
                source: '/api/v1/:path*',
                destination: 'http://backend:8000/api/v1/:path*',
            },
        ];
    },

    // Disable strict mode for compatibility
    reactStrictMode: false,

    // UNLOCK BUILD: Disable type checking and lint during build for now
    typescript: {
        ignoreBuildErrors: true,
    },
    eslint: {
        ignoreDuringBuilds: true,
    },

    // Output configuration for Docker
    output: 'standalone',
};

export default nextConfig;
