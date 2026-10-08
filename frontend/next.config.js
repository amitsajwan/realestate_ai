/** @type {import('next').NextConfig} */
const nextConfig = {
  // Search and link-preview bots get the title, description and canonical in <head> before the page streams. Next's own list
  // leaves Googlebot out (it runs JavaScript), but on a slow render the tags then land in <body>: an audit found 58 pages so.
  htmlLimitedBots: /Googlebot|Google-InspectionTool|Storebot-Google|[\w-]+-Google|Google-[\w-]+|Chrome-Lighthouse|Slurp|DuckDuckBot|baiduspider|yandex|sogou|bitlybot|tumblr|vkShare|quora link preview|redditbot|ia_archiver|Bingbot|BingPreview|applebot|facebookexternalhit|facebookcatalog|Twitterbot|LinkedInBot|Slackbot|Discordbot|WhatsApp|SkypeUriPreview|Yeti|googleweblight/i,
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