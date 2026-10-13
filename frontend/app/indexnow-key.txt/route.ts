import { serverApiBase } from '@/lib/site/api'

/** IndexNow's ownership proof: the key the backend sends with every batch of changed pages (backend/app/modules/seo/indexnow.py).
 *  404 while IndexNow is off or the backend is unreachable, so search engines never read a wrong key. */
export const dynamic = 'force-dynamic'

export async function GET(): Promise<Response> {
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/indexnow-key', { cache: 'no-store', signal: AbortSignal.timeout(5000) })
    const key = res.ok ? (await res.text()).trim() : ''
    if (/^[A-Za-z0-9-]{8,128}$/.test(key)) {
      return new Response(key, { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'public, max-age=3600' } })
    }
  } catch {
    // the backend is down: same answer as "off"
  }
  return new Response('Not found', { status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8' } })
}
