import React from 'react'
import { render, screen, within } from '@testing-library/react'
import ForAgentsPage, { metadata } from '@/app/for-agents/page'
import { FOR_AGENTS } from '@/app/for-agents/content'
import { encodeQr } from '@/lib/qr'
import { siteUrl } from '@/lib/brand'
import { socialLinks } from '@/lib/marketing/social'

const PHONE = /(?:\+?\d[\s\-().]*){10,}/

describe('/for-agents brochure', () => {
  it('has one h1 and every section, in the brochure order', () => {
    const { container } = render(<ForAgentsPage />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    const order = [/problem every agent knows/i, /four steps/i, /what you get/i, /what it costs/i, /what is coming/i, /keep it honest/i, /see it live/i, /request an invite/i]
    const h2s = Array.from(container.querySelectorAll('article h2')).map((h) => h.textContent || '')
    let at = -1
    for (const re of order) {
      const i = h2s.findIndex((t, k) => k > at && re.test(t))
      expect(i).toBeGreaterThan(at)
      at = i
    }
  })

  it('tells the create, attract, qualify, close story and what the agent gets', () => {
    const { container } = render(<ForAgentsPage />)
    const steps = Array.from(container.querySelectorAll('#how ol > li > p:first-child')).map((p) => (p.textContent || '').replace(/^\d/, '').trim())
    expect(steps).toEqual(['Create', 'Attract', 'Qualify', 'Close'])
    const text = container.textContent || ''
    for (const must of [/hindi voice/i, /tap-to-show-interest/i, /BHK, budget, timing/i, /RERA agent number/i, /listed by/i, /weekly results/i,
      /free during the pilot/i, /tell you before that changes/i, /own WhatsApp number/i, /once Meta approves/i,
      /nothing is sent to a buyer without you/i, /labelled as samples/i, /no invented AI percentages/i, /consent .* recorded/i]) {
      expect(text).toMatch(must)
    }
  })

  it('links to the invite form, the demo agent page, Instagram, /go and /news', () => {
    render(<ForAgentsPage />)
    const article = screen.getByRole('article')
    const hrefs = within(article).getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(hrefs).toEqual(expect.arrayContaining(['/request-invite', '/agent/demo', socialLinks().instagram, '/go', '/news']))
    expect(within(article).getAllByRole('link', { name: /request an invite/i }).length).toBeGreaterThanOrEqual(2)
  })

  it('prints the links as addresses and keeps the brand colours in print', () => {
    const { container } = render(<ForAgentsPage />)
    const host = siteUrl().replace(/^https?:\/\//, '')
    expect(container.textContent).toContain(host + '/agent/demo')
    expect(container.textContent).toContain(host + '/go')
    expect(screen.getByTestId('print-invite')).toHaveTextContent(host + '/request-invite')
    const css = container.querySelector('style')!.innerHTML
    expect(css).toMatch(/@media print/)
    expect(css).toMatch(/size: A4/)
    expect(css).toContain('.fa-root .bg-\\[\\#0f2340\\] { background-color: #0f2340 !important; }')
  })

  it('has a QR code for the invite page URL built from the site setting', () => {
    render(<ForAgentsPage />)
    const qr = screen.getByTestId('invite-qr')
    expect(qr.tagName.toLowerCase()).toBe('svg')
    expect(qr.getAttribute('data-value')).toBe(siteUrl() + '/request-invite')
    expect(qr.querySelector('path')!.getAttribute('d')!.length).toBeGreaterThan(500)
    expect(screen.getByText(FOR_AGENTS.cta.qr)).toBeInTheDocument()
  })

  it('shows no phone number and no invented social proof', () => {
    const { container } = render(<ForAgentsPage />)
    // the interim host (an IP-style sslip.io name) is an address, not a phone number
    const text = (container.textContent || '').split(siteUrl().replace(/^https?:\/\//, '')).join('<site>')
    expect(text).not.toMatch(PHONE)
    expect(container.querySelector('a[href^="tel:"]')).toBeNull()
    for (const banned of [/testimonial/i, /\brated\b/i, /trusted by/i, /\d+\s*%/, /\d+\s*\+?\s*(agents|customers|users|leads)\b/i, /guarantee/i]) {
      expect(text).not.toMatch(banned)
    }
  })

  it('has Hindi and Marathi one-line summaries and Avasetu metadata', () => {
    const { container } = render(<ForAgentsPage />)
    expect(container.querySelector('[lang="hi"]')!.textContent).toMatch(/[ऀ-ॿ]/)
    expect(container.querySelector('[lang="mr"]')!.textContent).toMatch(/[ऀ-ॿ]/)
    expect(String(metadata.title)).toMatch(/Avasetu/)
    expect(String(metadata.openGraph?.title)).toMatch(/Avasetu/)
  })
})

describe('QR encoder', () => {
  const finder = (m: boolean[][], x: number, y: number) => {
    for (let dy = 0; dy < 7; dy++)
      for (let dx = 0; dx < 7; dx++) {
        const ring = Math.max(Math.abs(dx - 3), Math.abs(dy - 3))
        expect(m[y + dy][x + dx]).toBe(ring !== 2)
      }
  }

  it('picks the smallest version and draws finder, timing and dark module', () => {
    expect(encodeQr('https://example.test/request-invite', 'M')).toHaveLength(29) // 35 bytes fit version 3 at M (42 max)
    const m = encodeQr('https://34-180-39-243.sslip.io/request-invite', 'M') // 46 bytes -> version 4 (62 bytes at M)
    const n = m.length
    expect(n).toBe(33)
    finder(m, 0, 0)
    finder(m, n - 7, 0)
    finder(m, 0, n - 7)
    for (let i = 8; i < n - 8; i++) {
      expect(m[6][i]).toBe(i % 2 === 0)
      expect(m[i][6]).toBe(i % 2 === 0)
    }
    expect(m[n - 8][8]).toBe(true)
  })

  it('writes a valid BCH-protected format word for level M', () => {
    const m = encodeQr('hello', 'M')
    let bits = 0
    const read = [[8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 7], [8, 8], [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8]]
    read.forEach(([x, y], i) => { if (m[y][x]) bits |= 1 << i })
    const data = (bits ^ 0x5412) >>> 10
    expect(data >>> 3).toBe(0) // M
    let rem = data
    for (let i = 0; i < 10; i++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537)
    expect(((data << 10) | rem) ^ 0x5412).toBe(bits)
  })
})
