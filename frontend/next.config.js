/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true
  },
  // Disable ESLint during build to avoid blocking deployment
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Enable standalone output for Docker (only in production)
  ...(process.env.NODE_ENV === 'production' && { output: 'standalone' }),
  // The owner's page moved from a personal-name address to the official Avasetu address; old links in posts keep working
  async redirects() {
    return [
      { source: '/agent/amit-sajwan', destination: '/agent/avasetu', permanent: true },
      { source: '/agent/amit-sajwan/:path*', destination: '/agent/avasetu/:path*', permanent: true },
      // House Deal's account moved from /agent/sharad to /agent/house-deal (2026-10-03); old post links keep working
      { source: '/agent/sharad', destination: '/agent/house-deal', permanent: true },
      { source: '/agent/sharad/:path*', destination: '/agent/house-deal/:path*', permanent: true },
    ]
  },
  // Proxy API requests to backend
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ]
  },
}

module.exports = nextConfig