// The dated opening of a project page, from the page's own facts (lib/site/projectFacts)
import { catalogAnswer, projectAnswer, projectUpdated, registerAnswer } from '@/lib/site/projectFacts'
import type { RegisterProject } from '@/lib/site/register'
import type { CatalogProject } from '@/lib/site/types'

const P: RegisterProject = {
  slug: 'rohan-abhilasha-4-wagholi', name: 'Rohan Abhilasha 4', regno: 'P52100080076', promoter: 'Rohan Builders', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-10-30', completion_at_registration: '2028-12-31',
  units_total: 416, units_booked: 244, details_read_at: '2026-10-03', listed_or_updated: '2026-09-28', maharera_url: null,
  paragraph: '', indexable: true, same_area: [], source: 'MahaRERA public records', page_updated: '2026-10-21',
}

describe('project page opening', () => {
  it('leads with the day the record was read, then number, possession and its move, bookings and the published price', () => {
    const prices = { read_at: '2026-10-20', rows: [{ bhk: '2 BHK', from_inr: 6900000, to_inr: null, official: false, sources: [{ site: '99acres', url: null }, { site: 'Housing', url: null }] }] }
    expect(registerAnswer({ ...P, prices })).toBe('As of 3 Oct 2026, Rohan Abhilasha 4 by Rohan Builders in Wagholi, Pune is registered with MahaRERA as '
      + 'P52100080076. The completion date filed with MahaRERA is 30 Oct 2029, moved from 31 Dec 2028 at registration. '
      + '244 of its 416 homes are booked. 2 BHK from ₹69 L, as listed on 99acres and Housing on 20 Oct 2026.')
  })

  it('says when MahaRERA\'s own order is in a move, so it does not read as a delay, and an agent\'s sheet is the one price', () => {
    const a = registerAnswer({ ...P, details: { extension_months: 4 } as never }, { from: '₹72 L', bhks: '2 & 3 BHK' })
    expect(a).toContain("(MahaRERA's August 2026 order added 4 months to most projects).")
    expect(a).toContain("2 & 3 BHK from ₹72 L on a local agent's price sheet.")
    expect(a).not.toContain('as listed on')
  })

  it('says only what it knows: no date, no bookings and no price when the page has none, and the OC once the date passed', () => {
    const a = projectAnswer({ name: 'X Homes', where: 'Kharadi, Pune', regno: 'P1', completionNow: '2025-06-30', completionAtRegistration: '2025-06-30', completionPassed: true })
    expect(a).toBe('X Homes in Kharadi, Pune is registered with MahaRERA as P1. The completion date filed with MahaRERA is 30 Jun 2025, '
      + 'not moved since registration. The filed completion date has passed: ask for the occupancy certificate (OC).')
    expect(projectAnswer({ name: 'Y', where: 'Wagholi, Pune', regno: 'P2', unitsTotal: 100, unitsBooked: 100 })).toContain('All 100 homes are booked.')
  })

  it('an agent-listed page reads its MahaRERA record and the agents\' price sheet', () => {
    const c = { name: 'Gera World of Joy', builder: 'Gera Developments', locality: 'Kharadi', rera_no: 'P52100011111', bhk_options: [2, 3],
      price_min: 9500000, updated_at: '2026-10-22T08:00:00Z',
      rera: { regno: 'P52100011111', completion_now: '2028-06-30', completion_at_registration: '2028-06-30', units_total: 300, units_booked: 120, checked_at: '2026-10-19' } } as unknown as CatalogProject
    expect(catalogAnswer(c)).toBe('As of 19 Oct 2026, Gera World of Joy by Gera Developments in Kharadi, Pune is registered with MahaRERA as '
      + "P52100011111. The completion date filed with MahaRERA is 30 Jun 2028, not moved since registration. 120 of its 300 homes are booked. "
      + "2 & 3 BHK from ₹95 L on the agent's price sheet.")
    expect(projectUpdated(c)).toBe('2026-10-22')
    expect(projectUpdated(P)).toBe('2026-10-21')
    expect(projectUpdated({ ...P, page_updated: null })).toBeNull()
  })
})
