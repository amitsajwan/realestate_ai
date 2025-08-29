/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true
  },
  // Allow ngrok origin for development
  allowedDevOrigins: ['aa828dedf50c.ngrok-free.app'],
}

module.exports = nextConfig
