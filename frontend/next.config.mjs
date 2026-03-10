/** @type {import('next').NextConfig} */
const nextConfig = {
    // Disable ESLint and Type-Checking during build to save time/memory on Railway
    eslint: {
        ignoreDuringBuilds: true,
    },
    typescript: {
        ignoreBuildErrors: true,
    }
};

export default nextConfig;
