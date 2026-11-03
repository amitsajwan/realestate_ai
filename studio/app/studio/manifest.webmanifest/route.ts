import { studioManifest } from '@/lib/app/manifest'

// Built once at build time: the manifest changes only with a deploy
export const dynamic = 'force-static'

export function GET() {
  return new Response(JSON.stringify(studioManifest()), {
    headers: { 'Content-Type': 'application/manifest+json; charset=utf-8', 'Cache-Control': 'public, max-age=3600' },
  })
}
