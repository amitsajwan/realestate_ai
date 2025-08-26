/** @type {import('next').NextConfig} */
const nextConfig = {
  // Removed 'output: export' for dynamic app with authentication
  // Removed 'trailingSlash: true' to prevent routing conflicts
  images: {
    unoptimized: true
  },
  // Allow ngrok origin for development
  allowedDevOrigins: ['aa828dedf50c.ngrok-free.app'],
}

module.exports = nextConfig
