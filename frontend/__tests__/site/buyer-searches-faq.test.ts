// What a portal's pages answer and ours did not (homebazaar.com read 2026-11-15): budget lists, the nearest hospital or school,
// the airport and the nearest work hub, and an EMI on the lowest published price
import { facetFaq } from '@/lib/site/facets'
import type { FacetPage } from '@/lib/site/facets'
import { distanceFaq } from '@/lib/site/register'
import { emiFor } from '@/lib/site/upfront'

describe('budget list FAQ', () => {
  const p = { intent: 'all', budget: 'under-50-lakh', budget_label: 'under 50 lakh', place: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' },
    rows: [{ name: 'Gagan Micasaa' }, { name: 'Equa' }], answer: 'As of 15 Nov 2026, 2 projects in Wagholi have flats under 50 lakh.',
    as_of: '2026-11-15' } as unknown as FacetPage

  it('asks the budget search and says the price is not the full cost', () => {
    const qs = facetFaq(p)
    expect(qs[0].q).toBe('Which new projects in Wagholi, Pune have flats under 50 lakh?')
    expect(qs[0].a).toContain('Cheapest first: Gagan Micasaa, Equa.')
    expect(qs[1].a).toContain('stamp duty and registration usually come on top')
  })
})

describe('distance questions on a project page', () => {
  const nearby = [
    { label: 'School', name: 'Lexicon International School', km: 0.8 },
    { label: 'Hospital', name: 'Lifeline Hospital', km: 1.6 },
    { label: 'Hospital', name: 'Columbia Asia', km: 4.2 },
  ]
  const commute = [{ name: 'EON IT Park, Kharadi', km: 7.4 }, { name: 'Pune Airport (Lohegaon)', km: 9 }, { name: 'Pune Railway Station', km: 14.2 }]

  it('names the nearest place of each kind measured, the airport and the nearest work hub, with the distance as measured', () => {
    const qs = distanceFaq({ commute }, 'Springshire', nearby)
    expect(qs.map((f) => f.q)).toEqual([
      'Which hospital is nearest to Springshire?', 'Which school is nearest to Springshire?',
      'How far is Springshire from Pune Airport?', 'How far is Springshire from EON IT Park, Kharadi?',
    ])
    expect(qs[0].a).toBe('Lifeline Hospital, about 1.6 km away in a straight line from the map position; the drive is longer.')
    expect(qs[2].a).toContain('About 9 km')
  })

  it('asks nothing it has no measured place for', () => {
    expect(distanceFaq({ commute: [] }, 'X', [])).toEqual([])
  })
})

describe('EMI on a published price', () => {
  it('is 80% of the price at 8.5% over 20 years, as the offer card states it', () => {
    expect(emiFor(8_000_000)).toEqual({ emi: 55_541, loan: 6_400_000, rate: 8.5, years: 20 })
    expect(emiFor(0)).toBeNull()
  })
})
