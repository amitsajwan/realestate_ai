import React from 'react'
import { render, screen, within } from '@testing-library/react'
import HotStrip, { HotStripView } from '@/components/site/HotStrip'
import type { SpotlightProject } from '@/lib/site/hubs'

const p = (slug: string, extra: Partial<SpotlightProject> = {}): SpotlightProject => ({
  slug, name: slug.replace(/-/g, ' '), area: 'Kharadi', area_slug: 'kharadi', note: null, fact: '42 homes booked in 90 days',
  source: 'MahaRERA', picked: false, regnos: [], ...extra,
})

function answer(spotlight: SpotlightProject[], catalog: unknown[] = []) {
  global.fetch = jest.fn(async (url: string) => {
    const body = String(url).includes('/register/spotlight') ? spotlight : { items: catalog }
    return { ok: true, status: 200, json: async () => body } as Response
  }) as unknown as typeof fetch
}

describe('hot projects banner', () => {
  it('is plain crawlable links, the loop copy hidden from screen readers and the tab order', () => {
    render(<HotStripView items={[p('camelot-kharadi', { note: 'New tower registered' }), p('abhilasha-wagholi', { area: 'Wagholi' })]} areaName="Kharadi" />)
    const strip = screen.getByTestId('hot-strip')
    expect(strip.tagName).toBe('ASIDE')
    expect(strip).toHaveAttribute('aria-label', 'Hot in Kharadi')
    expect(within(strip).queryByRole('heading')).toBeNull()   // adds no headings to the page
    const links = screen.getAllByTestId('hot-strip-link')
    expect(links.map((a) => a.getAttribute('href'))).toEqual(['/projects/camelot-kharadi', '/projects/abhilasha-wagholi'])
    expect(links[0]).toHaveTextContent('New tower registered')                  // the owner's note wins
    expect(links[1]).toHaveTextContent('42 homes booked in 90 days (MahaRERA)') // else a sourced fact
    expect(links[1]).toHaveTextContent('· Wagholi')                             // another area is named
    const copy = strip.querySelectorAll('ul')[1]
    expect(copy).toHaveAttribute('aria-hidden', 'true')
    copy.querySelectorAll('a').forEach((a) => expect(a).toHaveAttribute('tabindex', '-1'))
  })

  it('is hidden when there is nothing to show, and says Pune when the first project is elsewhere', () => {
    const { container, rerender } = render(<HotStripView items={[]} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<HotStripView items={[p('busy-wagholi', { area: 'Wagholi' })]} areaName="Kharadi" />)
    expect(screen.getByTestId('hot-strip')).toHaveAttribute('aria-label', 'Hot in Pune')
    expect(screen.getByTestId('hot-strip').querySelectorAll('ul')).toHaveLength(1)   // one project: nothing to loop
  })

  it("links an agent-listed project's shared page (never through a redirect) and leaves out the page's own project", async () => {
    answer([p('camelot-kharadi', { regnos: ['P1', 'P1T2'] }), p('quiet-kharadi'), p('own-page')],
      [{ slug: 'lodha-camelot', rera_no: 'P1T2', agents: [{ slug: 'a' }] }, { slug: 'unlisted', rera_no: 'P9', agents: [] }])
    render(await HotStrip({ area: 'kharadi', exclude: 'own-page' }))
    expect(screen.getAllByTestId('hot-strip-link').map((a) => a.getAttribute('href'))).toEqual(['/projects/lodha-camelot', '/projects/quiet-kharadi'])
    expect(String((global.fetch as jest.Mock).mock.calls[0][0])).toContain('/api/v1/public/register/spotlight?area=kharadi')
  })

  it('never breaks a page when the API is down', async () => {
    global.fetch = jest.fn(async () => { throw new Error('down') }) as unknown as typeof fetch
    const { container } = render(await HotStrip({}))
    expect(container).toBeEmptyDOMElement()
  })
})

describe('hot projects banner speed', () => {
  it('rolls at a reading pace: about 80 s for six usual entries, longer for longer text, never under 20 s', async () => {
    const { rollSeconds } = await import('@/components/site/HotStrip')
    const six = Array.from({ length: 6 }, (_, i) => p(`project-${i}-kharadi`, { name: 'Lodha Camelot Tower ' + i, fact: '42 homes booked in the last 90 days' }))
    const secs = rollSeconds(six)
    expect(secs).toBeGreaterThanOrEqual(60)
    expect(secs).toBeLessThanOrEqual(110)
    expect(rollSeconds([...six, ...six])).toBeGreaterThan(secs)
    expect(rollSeconds([p('x', { name: 'A', fact: 'b', source: 'c', area: null })])).toBe(20)
  })

  it('puts the loop length on the track', () => {
    render(<HotStripView items={[p('a-kharadi'), p('b-kharadi')]} />)
    const track = screen.getByTestId('hot-strip').querySelector('.hot-strip-track') as HTMLElement
    expect(track.style.getPropertyValue('--hot-roll')).toMatch(/^\d+s$/)
  })
})
