const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  // shared/ at the repo root holds the plain TypeScript the site and Studio both use (brand, site types, localities, strings)
  experimental: { externalDir: true },
  turbopack: { root: path.join(__dirname, '..') },
  // ...but the server bundle is built from this folder alone (shared/ is compiled in), so .next/standalone/server.js stays flat
  outputFileTracingRoot: __dirname,
  // Search and link-preview bots get the title, description and canonical in <head> before the page streams. Next's own list
  // leaves Googlebot out (it runs JavaScript), but on a slow render the tags then land in <body>: an audit found 58 pages so.
  // AI fetchers too (2026-11-02): they read no JavaScript and quote the page's title.
  htmlLimitedBots: /OAI-SearchBot|ChatGPT-User|GPTBot|PerplexityBot|Perplexity-User|Claude-User|Claude-SearchBot|ClaudeBot|Googlebot|Google-InspectionTool|Storebot-Google|[\w-]+-Google|Google-[\w-]+|Chrome-Lighthouse|Slurp|DuckDuckBot|baiduspider|yandex|sogou|bitlybot|tumblr|vkShare|quora link preview|redditbot|ia_archiver|Bingbot|BingPreview|applebot|facebookexternalhit|facebookcatalog|Twitterbot|LinkedInBot|Slackbot|Discordbot|WhatsApp|SkypeUriPreview|Yeti|googleweblight/i,
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
      // the fictional demo agent page was removed (owner 2026-10-30); printed /for-agents QR codes and old links land on a real one
      { source: '/agent/demo', destination: '/agent/house-deal', permanent: true },
      { source: '/agent/demo/:path*', destination: '/agent/house-deal', permanent: true },
      { source: '/agent/sharad/:path*', destination: '/agent/house-deal/:path*', permanent: true },
      // the owner places Esbee's upcoming project in Wagholi (2026-11-02); shared links to the old address keep working
      { source: '/projects/upcoming/esbee-upper-kharadi', destination: '/projects/upcoming/esbee-wagholi', permanent: true },
      // the agents' home moved from / to /agents (2026-10-22); /agent with no name is the address people guess for it
      { source: '/agent', destination: '/agents', permanent: true },
      // the old email/password app (its 'Forgot password' link was a 404): sign-in is the login code at /join, the app is /studio
      { source: '/login', destination: '/join', permanent: false },
      { source: '/register', destination: '/join', permanent: false },
      { source: '/forgot-password', destination: '/join', permanent: false },
      { source: '/dashboard', destination: '/studio', permanent: false },
      { source: '/onboarding', destination: '/studio', permanent: false },
      { source: '/profile', destination: '/studio', permanent: false },
    ]
  },
  // Proxy API requests to backend
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
      // Studio is its own app (studio/, `npm run dev` there on port 3001). Locally the site hands it Studio's addresses so both
      // run on one origin and share the login; in production Caddy routes them before they reach the site (deploy/gcp/Caddyfile).
      ...(process.env.NODE_ENV === 'production' ? [] : ['/studio', '/studio/:path*', '/studio-static/:path*', '/join'].map((source) => ({
        source,
        destination: `${process.env.STUDIO_DEV_URL || 'http://localhost:3001'}${source}`,
      }))),
    ]
  },
}

module.exports = nextConfig