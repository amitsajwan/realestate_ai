// The top list says how it is ranked, as the backend ranks it (backend seo/facets._top, 2026-11-03)
import { facetFaq } from '@/lib/site/facets'
import type { FacetPage } from '@/lib/site/facets'

describe('top list FAQ', () => {
  const p = { intent: 'top', place: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, rows: [{ name: 'Flamante' }, { name: 'Equa' }],
    answer: 'As of 3 Nov 2026, 2 projects in Wagholi still have 10 or more homes open on MahaRERA.', as_of: '2026-11-03', sold_out_count: 0 } as unknown as FacetPage

  it('says the list is one row per project, ranked by homes booked a month, from the builders\' quarterly counts', () => {
    const ranked = facetFaq(p).find((f) => f.q === 'How is this list ranked?')!.a
    expect(ranked).toContain('one row per project however many MahaRERA registrations it has')
    expect(ranked).toContain('else by homes booked a month since registration')
    expect(ranked).toContain("MahaRERA's counts are the builders' own, filed each quarter")
    expect(ranked).not.toContain('share of homes booked')
  })
})
