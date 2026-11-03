const path = require('path')

/**
 * Studio (/studio and its sign-in /join) is its own Next.js app, deployed apart from the public site (frontend/). On avasetu.in
 * Caddy sends /studio, /join and /studio-static to this app and every other page to the site (deploy/gcp/Caddyfile), so both
 * share one address and one login (the token in localStorage). Next.js calls this layout "multi-zones".
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  // this app's scripts and styles live under /studio-static/_next/..., apart from the site's /_next/...
  assetPrefix: '/studio-static',
  images: { unoptimized: true },
  // shared/ at the repo root holds the plain TypeScript the site and Studio both use (brand, site types, localities, strings)
  experimental: { externalDir: true },
  turbopack: { root: path.join(__dirname, '..') },
  // ...but the server bundle is built from this folder alone (shared/ is compiled in), so .next/standalone/server.js stays flat
  outputFileTracingRoot: __dirname,
  ...(process.env.NODE_ENV === 'production' && { output: 'standalone' }),
  // Running on its own (npm run dev, port 3001): the API goes to the local backend. Locally the site (port 3000) forwards
  // /studio, /join and /studio-static here, so open the site's address to use both on one origin.
  async rewrites() {
    return [{ source: '/api/v1/:path*', destination: `${process.env.STUDIO_DEV_API_URL || 'http://localhost:8000'}/api/v1/:path*` }]
  },
}

module.exports = nextConfig
