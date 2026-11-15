// The "Checked on MahaRERA" badge agents put on their sites (docs/plan/visibility-base.md step 3)
// jsdom has no Response: a minimal stand-in reads the body, the status and the headers
;(global as any).Response = class {
  body: string; status: number; headers: Headers
  constructor(b: string, init: any) { this.body = b; this.status = init?.status ?? 200; this.headers = new Headers(init?.headers) }
  async text() { return this.body }
}
const getRegister = jest.fn()
jest.mock('@/lib/site/register', () => ({
  getRegisterProjectByRegno: (n: string) => getRegister(n),
  displayName: (p: { marketed_name?: string; name: string }) => p.marketed_name || p.name,
}))

import { GET } from '@/app/badge/[file]/route'
import { badgeEmbed, badgeMonth, badgeName, badgeSvg } from '@/lib/site/badge'

const call = (file: string) => GET({} as Request, { params: Promise.resolve({ file }) })

describe('badge', () => {
  beforeEach(() => getRegister.mockReset())

  it('draws the project, its MahaRERA number and the month we read it, escaped', () => {
    const svg = badgeSvg({ name: 'Rohan <Abhilasha> & Co', regno: 'P52100012345', checked: '2026-11-14' })
    expect(svg).toContain('Checked on MahaRERA')
    expect(svg).toContain('Rohan &lt;Abhilasha&gt; &amp; Co')
    expect(svg).toContain('P52100012345 · read Nov 2026 · Avasetu')
    expect(badgeName('Kolte Patil Life Republic Sector R10 Phase 2')).toBe('Kolte Patil Life Republic…')
    expect(badgeMonth('bad')).toBe('')
  })

  it('links the badge to the project page with a followed link', () => {
    const html = badgeEmbed('https://avasetu.in/', 'godrej-ivara-pune', 'PR1260002502426', 'Godrej Ivara')
    expect(html).toBe('<a href="https://avasetu.in/projects/godrej-ivara-pune" title="Godrej Ivara on MahaRERA, checked by Avasetu">'
      + '<img src="https://avasetu.in/badge/PR1260002502426.svg" width="300" height="64" alt="Godrej Ivara: checked on MahaRERA (PR1260002502426)" /></a>')
    expect(html).not.toContain('nofollow')
  })

  it('serves an SVG for a number in our register and a 404 for any other', async () => {
    getRegister.mockResolvedValue({ name: 'GODREJ IVARA', marketed_name: 'Godrej Ivara', regno: 'PR1260002502426', details_read_at: '2026-11-14' })
    const ok = await call('pr1260002502426.svg')
    expect(ok.status).toBe(200)
    expect(ok.headers.get('content-type')).toContain('image/svg+xml')
    expect(await ok.text()).toContain('Godrej Ivara')
    expect(getRegister).toHaveBeenCalledWith('PR1260002502426')
    getRegister.mockResolvedValue(null)
    expect((await call('P52100099999.svg')).status).toBe(404)
    expect((await call('not-a-number.svg')).status).toBe(404)
  })
})
