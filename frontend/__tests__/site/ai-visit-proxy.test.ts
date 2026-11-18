// The proxy forwards only requests that may be AI fetchers or visitors from AI answers (backend app/modules/seo/aivisits.py).
// jsdom has no Request: a request is its headers and URL, the response a marker
jest.mock('next/server', () => ({ NextResponse: { next: () => 'next' } }))
import type { NextFetchEvent, NextRequest } from 'next/server'
import { proxy, shouldLog } from '@/proxy'

function req(url: string, headers: Record<string, string>): NextRequest {
  const u = new URL(url)
  return { headers: { get: (k: string) => headers[k.toLowerCase()] ?? null }, nextUrl: u } as unknown as NextRequest
}

const CHROME = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36'

describe('which requests the AI visit log sees', () => {
  it('sends AI fetchers, AI referrals and tagged links, never ordinary or internal visits', () => {
    expect(shouldLog('Mozilla/5.0; compatible; ChatGPT-User/1.0', '', 'avasetu.in', null)).toBe(true)
    expect(shouldLog('Mozilla/5.0 (compatible; bingbot/2.0)', '', 'avasetu.in', null)).toBe(true)
    expect(shouldLog(CHROME, 'https://chatgpt.com/', 'avasetu.in', null)).toBe(true)
    expect(shouldLog(CHROME, '', 'avasetu.in', 'chatgpt.com')).toBe(true)
    expect(shouldLog(CHROME, '', 'avasetu.in', null)).toBe(false)
    expect(shouldLog(CHROME, 'https://avasetu.in/projects', 'avasetu.in', null)).toBe(false)
  })

  it('sends every other robot too, so we can see who reads the site', () => {
    for (const ua of ['Mozilla/5.0 (compatible; Google-InspectionTool/1.0;)', 'Mozilla/5.0 (compatible; AhrefsBot/7.0)', 'facebookexternalhit/1.1',
      'WhatsApp/2.23.20.0', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/157.0 Safari/537.36',
      'python-requests/2.31', 'curl/8.5.0', 'Mozilla/5.0 (Linux; Android 11; moto g power) Chrome-Lighthouse']) {
      expect(shouldLog(ua, '', 'avasetu.in', null)).toBe(true)
    }
    expect(shouldLog('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Instagram 300.0', '', 'avasetu.in', null)).toBe(false)
  })

  it('posts to the internal endpoint after the response and never on prefetches', async () => {
    const calls: [string, RequestInit][] = []
    global.fetch = jest.fn(async (url: string, init: RequestInit) => { calls.push([url, init]); return { ok: true, status: 204 } }) as unknown as typeof fetch
    const waits: Promise<unknown>[] = []
    const event = { waitUntil: (p: Promise<unknown>) => waits.push(p) } as unknown as NextFetchEvent
    process.env.SITE_API_URL = 'http://backend:8000'
    const res = proxy(req('https://avasetu.in/projects/area/lohegaon/2-bhk?utm_source=chatgpt.com', { 'user-agent': CHROME, host: 'avasetu.in' }), event)
    expect(res).toBe('next')
    await Promise.all(waits)
    expect(calls[0][0]).toBe('http://backend:8000/internal/seo/visit')
    expect(JSON.parse(String(calls[0][1].body))).toEqual({ ua: CHROME, referer: '', path: '/projects/area/lohegaon/2-bhk', utm_source: 'chatgpt.com' })

    calls.length = 0
    proxy(req('https://avasetu.in/projects', { 'user-agent': 'GPTBot', rsc: '1' }), event)
    expect(calls).toHaveLength(0)
  })
})
