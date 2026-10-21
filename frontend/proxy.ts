import { NextResponse } from 'next/server'
import type { NextFetchEvent, NextRequest } from 'next/server'

/**
 * AI search visit log (backend app/modules/seo/aivisits.py, docs/plan/seo-system.md "AI search"): a page request that may be an AI
 * fetcher (ChatGPT-User, OAI-SearchBot, PerplexityBot, Bingbot ...) or a visitor from an AI answer (chatgpt.com, perplexity.ai,
 * utm_source=chatgpt.com) is sent to the backend's /internal/seo/visit after the response, which keeps only what it recognises.
 * Never delays or changes the page; any failure is dropped. Ordinary visitors from Google or typed URLs are not sent at all.
 */
const MAYBE_AI_UA = /bot|gpt|perplexity|claude|crawler|spider|google-extended|meta-externalagent|cohere|mistral|duckassist/i

function ownHost(host: string | null, referer: string): boolean {
  try {
    return !!host && new URL(referer).host === host
  } catch {
    return true
  }
}

export function shouldLog(ua: string, referer: string, host: string | null, utmSource: string | null): boolean {
  return MAYBE_AI_UA.test(ua) || !!utmSource || (!!referer && !ownHost(host, referer))
}

export function proxy(request: NextRequest, event: NextFetchEvent) {
  // client-side navigations and prefetches are not page loads
  if (request.headers.get('rsc') || request.headers.get('next-router-prefetch') || request.headers.get('purpose') === 'prefetch') {
    return NextResponse.next()
  }
  const ua = request.headers.get('user-agent') || ''
  const referer = request.headers.get('referer') || ''
  const utm = request.nextUrl.searchParams.get('utm_source')
  if (shouldLog(ua, referer, request.headers.get('host'), utm)) {
    const base = (process.env.SITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')
    event.waitUntil(
      fetch(`${base}/internal/seo/visit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ua: ua.slice(0, 500), referer: referer.slice(0, 500), path: request.nextUrl.pathname.slice(0, 500), utm_source: utm?.slice(0, 80) ?? null }),
        signal: AbortSignal.timeout(2000),
      }).then(() => undefined, () => undefined),
    )
  }
  return NextResponse.next()
}

export const config = {
  // pages, robots.txt and llms.txt; never the app's assets, images, the API or the sitemaps
  matcher: ['/((?!_next/|api/|uploads/|sitemaps/|.*\\.(?:png|jpe?g|gif|webp|avif|svg|ico|css|js|map|woff2?|ttf|xml|json)$).*)'],
}
