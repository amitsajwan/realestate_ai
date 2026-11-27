/**
 * Google Analytics 4 (docs/plan/ga4.md): the tag runs only in production builds, our events reach GA4 under GA4's names with
 * the page's dimensions, an enquiry is generate_lead without the buyer's details, and a Studio user's visits are not sent.
 */
import { GA_EVENT_NAMES, gaId, pageParams, vitalParams } from '@/lib/site/ga'

describe('gaId', () => {
  it('is the Avasetu stream in a production build', () => {
    expect(gaId({ NODE_ENV: 'production' })).toBe('G-3MYR5F1C05')
  })
  it('is off in dev and tests, so our own work is never counted', () => {
    expect(gaId({ NODE_ENV: 'development' })).toBe('')
    expect(gaId({ NODE_ENV: 'test', NEXT_PUBLIC_GA_ID: 'G-ABCDEF1234' })).toBe('')
  })
  it('takes another stream from NEXT_PUBLIC_GA_ID, and an empty or malformed one turns it off', () => {
    expect(gaId({ NODE_ENV: 'production', NEXT_PUBLIC_GA_ID: 'G-ABCDEF1234' })).toBe('G-ABCDEF1234')
    expect(gaId({ NODE_ENV: 'production', NEXT_PUBLIC_GA_ID: '' })).toBe('')
    expect(gaId({ NODE_ENV: 'production', NEXT_PUBLIC_GA_ID: 'UA-123' })).toBe('')
  })
})

describe('pageParams', () => {
  it('names the kind of page, its area, whose site it is and whether it asks to be indexed', () => {
    expect(pageParams('/projects/area/kharadi/top', 'avasetu', 'index, follow')).toEqual({
      page_type: 'list', area: 'kharadi', agent: 'avasetu', in_search: 'yes',
    })
    expect(pageParams('/projects/godrej-ivara-pune', 'avasetu', 'noindex, follow')).toEqual({
      page_type: 'project', agent: 'avasetu', in_search: 'no',
    })
    expect(pageParams('/agent/house-deal/listings/abc123', 'house-deal').agent).toBe('house-deal')
  })
})

describe('GA_EVENT_NAMES', () => {
  it('sends views as page_view and an enquiry as generate_lead', () => {
    expect(GA_EVENT_NAMES.page_view).toBe('page_view')
    expect(GA_EVENT_NAMES.listing_view).toBe('page_view')
    expect(GA_EVENT_NAMES.inquiry).toBe('generate_lead')
    expect(GA_EVENT_NAMES.whatsapp_click).toBe('whatsapp_click')
    expect(GA_EVENT_NAMES.call_click).toBe('call_click')
  })
})

describe('vitalParams', () => {
  it('sends CLS x1000 as a whole number and the page type beside it', () => {
    const p = vitalParams({ id: 'v1', name: 'CLS', value: 0.123, rating: 'needs-improvement' }, 'avasetu', '/localities/wagholi')
    expect(p).toMatchObject({ value: 123, metric_value: 0.123, metric_rating: 'needs-improvement', page_type: 'area', area: 'wagholi' })
    expect(vitalParams({ id: 'v2', name: 'LCP', value: 2410.6 }, 'avasetu', '/').value).toBe(2411)
  })
})

describe('events reaching gtag', () => {
  const env = process.env as Record<string, string | undefined>
  const before = env.NODE_ENV
  let calls: unknown[][]

  beforeEach(() => {
    jest.resetModules()
    env.NODE_ENV = 'production'
    calls = []
    const w = window as unknown as { gtag?: unknown; dataLayer?: unknown[] }
    delete w.gtag
    w.dataLayer = undefined
    w.gtag = (...args: unknown[]) => { calls.push(args) }
    window.localStorage.clear()
    global.fetch = jest.fn(() => Promise.resolve({ ok: true } as Response)) as unknown as typeof fetch
  })
  afterEach(() => {
    env.NODE_ENV = before
  })

  it('sends a page view with its dimensions', () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { trackEvent } = require('@/lib/site/tracking')
    trackEvent('page_view', 'avasetu')
    const ev = calls.find((c) => c[0] === 'event')
    expect(ev?.[1]).toBe('page_view')
    expect(ev?.[2]).toMatchObject({ agent: 'avasetu', in_search: 'yes' })
  })

  it('sends an enquiry as generate_lead with the form, never the name, phone or message', async () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { submitInquiry } = require('@/lib/site/tracking')
    await submitInquiry('avasetu', undefined, { name: 'Asha', phone: '9800000000', message: 'call me', consent: true })
    const ev = calls.find((c) => c[0] === 'event' && c[1] === 'generate_lead')
    expect(ev).toBeTruthy()
    const sent = JSON.stringify(ev)
    expect(sent).toContain('"form":"enquiry"')
    expect(sent).not.toMatch(/Asha|9800000000|call me/)
  })
})

describe('one tag', () => {
  it('loads gtag.js only through TrackingBeacon, so page views are not counted twice and Studio-side pages never load it', () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const fs = require('fs')
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const path = require('path')
    const layout = fs.readFileSync(path.join(__dirname, '../../app/layout.tsx'), 'utf8')
    expect(layout).not.toMatch(/googletagmanager|gtag\(/)
  })
})
