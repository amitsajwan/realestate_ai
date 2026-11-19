// Thin new projects were left out of every list, so a buyer never found them. Owner 2026-11-19: show them on one common page ("our
// team is working on these new projects ... this is what we have now"), and each such page says what it does not have yet.
import { render, screen } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { detailsComing, missingDetails, sayList } from '@/lib/site/detailsComing'
import type { RegisterListItem, RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <section id="enquire" /> }))

const item = (slug: string, over: Partial<RegisterListItem> = {}): RegisterListItem => ({
  slug, regno: 'P' + slug.toUpperCase().replace(/-/g, ''), name: slug, area: 'kharadi', completion_now: '2030-06-30',
  listed_or_updated: '2026-11-01', indexable: false, ...over,
})

describe('the details-coming list', () => {
  it('holds our areas\' building projects not in search, newest first, and none that are in search, finished, sold out or offered', () => {
    const groups = detailsComing([
      item('older', { listed_or_updated: '2026-09-01' }), item('newer', { listed_or_updated: '2026-11-10' }),
      item('in-search', { indexable: true }), item('finished', { active: false }), item('sold', { sold_out: true }),
      item('elsewhere', { area: null }), item('offered'), item('wagholi-one', { area: 'wagholi' }),
    ], new Set([item('offered').regno]))
    expect(groups.map((g) => [g.area, g.items.map((r) => r.slug)])).toEqual([['Kharadi', ['newer', 'older']], ['Wagholi', ['wagholi-one']]])
  })
})

const P: RegisterProject = {
  slug: 'new-heights-wagholi', name: 'New Heights', regno: 'P52100022222', promoter: 'B', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-10-30', completion_at_registration: '2029-10-30',
  units_total: 100, units_booked: 10, details_read_at: '2026-11-03', listed_or_updated: '2026-11-01', completion_passed: false,
  maharera_url: null, paragraph: 'New Heights is a project in Wagholi.', indexable: false, source: 'MahaRERA public records', same_area: [],
}
const PRICES = { read_at: '2026-11-03', rows: [{ bhk: '2 BHK', from_inr: 6_500_000, to_inr: null, official: true, sources: [] }] }
const PHOTO = { url: '/uploads/a.jpg', width: 800, height: 600, alt: 'a', site: 'b.com', page_url: null, source: 'builder' as const }

describe('a project page not in search yet', () => {
  it('says our team is still collecting details and names what is missing', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    const note = screen.getByTestId('details-coming')
    expect(note).toHaveTextContent('Our team is still collecting details on New Heights')
    expect(note).toHaveTextContent("We do not have prices, the builder's pictures and floor plans yet")
    expect(screen.getByText('Other new projects we are reading').closest('a')).toHaveAttribute('href', '/projects/details-coming')
  })

  it('has no note in search, finished, or holding everything while it waits its turn', () => {
    const full = { ...P, prices: PRICES, profile: { read_at: null, highlights: [], photos: [PHOTO], plans: [PHOTO] } }
    for (const p of [{ ...P, indexable: true }, { ...P, finished: true }, full]) {
      const { unmount } = render(<RegisterProjectPage p={p} siteUrl="https://avasetu.in" facts={null} />)
      expect(screen.queryByTestId('details-coming')).not.toBeInTheDocument()
      unmount()
    }
  })

  it('does not count an AI drawing as the builder\'s pictures', () => {
    expect(missingDetails({ prices: PRICES, profile: { read_at: null, highlights: [], photos: [{ ...PHOTO, source: 'ai' }], plans: [] } }))
      .toEqual(["the builder's pictures", 'floor plans'])
    expect(sayList(['prices'])).toBe('prices')
  })
})

describe('the details-coming page itself', () => {
  it('is in search, under a title that does not compete with /projects (owner 2026-11-19)', async () => {
    const { generateMetadata } = await import('@/app/projects/details-coming/page')
    const meta = generateMetadata()
    expect(meta.robots).toBeUndefined()
    expect(String(meta.title)).toMatch(/^Newly Registered MahaRERA Projects in Pune/)
    expect(require('fs').readFileSync(require('path').join(__dirname, '../../lib/site/sitemap.ts'), 'utf8')).toMatch(/core\(at\(DETAILS_COMING_PATH/)
  })
})
