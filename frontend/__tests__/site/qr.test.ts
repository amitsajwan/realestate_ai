// The printable QR card for a project page (docs/plan/visibility-base.md step 4): scans open the page tagged src=qr
// jsdom has no TextEncoder, which the qrcode package uses for the bytes of the link (Node and the server have it)
import { TextEncoder } from 'util'
;(global as any).TextEncoder ??= TextEncoder
;(global as any).Response = class {
  body: string; status: number; headers: Headers
  constructor(b: string, init: any) { this.body = b; this.status = init?.status ?? 200; this.headers = new Headers(init?.headers) }
  async text() { return this.body }
}
const getProject = jest.fn()
jest.mock('@/lib/site/register', () => ({
  getRegisterProject: (s: string) => getProject(s),
  displayName: (p: { marketed_name?: string; name: string }) => p.marketed_name || p.name,
}))
jest.mock('@/lib/marketing/config', () => ({ getMarketingConfig: () => ({ siteUrl: 'https://avasetu.in' }) }))

import QRCode from 'qrcode'
import { GET } from '@/app/qr/[file]/route'
import { qrSvg, qrTarget } from '@/lib/site/qr'
import { qrUrl } from '@shared/site/badge'

const call = (file: string) => GET({} as Request, { params: Promise.resolve({ file }) })

describe('project QR card', () => {
  beforeEach(() => getProject.mockReset())

  it('opens the project page tagged as a scan, so those visits count as "QR code"', () => {
    expect(qrTarget('https://avasetu.in/', 'godrej-ivara-pune')).toBe('https://avasetu.in/projects/godrej-ivara-pune?src=qr')
    expect(qrUrl('https://avasetu.in', 'godrej-ivara-pune')).toBe('https://avasetu.in/qr/godrej-ivara-pune.svg')
  })

  it('draws every dark module of the code, and the name escaped under it', () => {
    const url = 'https://avasetu.in/projects/godrej-ivara-pune?src=qr'
    const svg = qrSvg({ url, name: 'Rohan <Abhilasha> & Co', regno: 'P52100012345' })
    const { modules } = QRCode.create(url, { errorCorrectionLevel: 'M' })
    const dark = Array.from(modules.data).filter(Boolean).length
    expect(svg.match(/h8v8h-8z/g)?.length).toBe(dark)
    expect(svg).toContain('Rohan &lt;Abhilasha&gt; &amp; Co')
    expect(svg).toContain('MahaRERA P52100012345 · avasetu.in')
  })

  it('serves a card for a project we hold, out of search, and a 404 for anything else', async () => {
    getProject.mockResolvedValue({ slug: 'godrej-ivara-pune', name: 'GODREJ IVARA', marketed_name: 'Godrej Ivara', regno: 'P52100055555' })
    const ok = await call('godrej-ivara-pune.svg')
    expect(ok.status).toBe(200)
    expect(ok.headers.get('Content-Type')).toContain('image/svg+xml')
    expect(ok.headers.get('X-Robots-Tag')).toBe('noindex')
    expect(await ok.text()).toContain('Godrej Ivara')
    getProject.mockResolvedValue(null)
    expect((await call('nobody.svg')).status).toBe(404)
    expect((await call('../etc.svg')).status).toBe(404)
  })
})

import { readAttribution } from '@/lib/site/tracking'

describe('a paid click keeps its click id', () => {
  it('reads gclid with the utm tags, so the backend can name it Google Ads', () => {
    expect(readAttribution('?gclid=Cj0KCQ&utm_source=google&x=1').utm).toEqual({ gclid: 'Cj0KCQ', utm_source: 'google' })
  })
})
