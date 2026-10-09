import { siteUrl } from '@/lib/brand'
import { serverApiBase } from '@/lib/site/api'

/**
 * The short link in a radar reply (backend radar/router.py `GET /radar/r/{code}`): the API credits the click to that lead and
 * says where it lands (a project's MahaRERA page, a listing, or an area page). Only our own pages are redirected to.
 */
export async function GET(request: Request, ctx: { params: Promise<{ code: string }> }) {
  const { code } = await ctx.params
  const here = new URL(request.url)
  let target = '/localities'
  try {
    const res = await fetch(serverApiBase() + '/api/v1/radar/r/' + encodeURIComponent(code.slice(0, 20)), { cache: 'no-store' })
    if (res.ok) {
      const { url } = (await res.json()) as { url?: string }
      if (url) {
        const u = new URL(url, here.origin)
        if (u.host === here.host || u.host === new URL(siteUrl()).host) target = u.pathname + u.search + u.hash
      }
    }
  } catch {
    // the API being down still sends the visitor somewhere useful
  }
  return new Response(null, { status: 302, headers: { Location: target, 'Cache-Control': 'no-store' } })
}
