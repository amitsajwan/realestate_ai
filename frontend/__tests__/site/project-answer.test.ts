// The dated opening of a project page, from the page's own facts (lib/site/projectFacts)
import { catalogAnswer, projectAnswer, projectUpdated, registerAnswer } from '@/lib/site/projectFacts'
import { askedPrices, completionChange, headingName, monthsApart, projectFaq } from '@/lib/site/register'
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
      + 'MahaRERA shows 244 of 416 homes booked. 2 BHK from ₹69 L, as listed on 99acres and Housing on 20 Oct 2026.')
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
    expect(projectAnswer({ name: 'Y', where: 'Wagholi, Pune', regno: 'P2', unitsTotal: 100, unitsBooked: 100 })).toContain('MahaRERA shows all 100 homes booked.')
  })

  it('an agent-listed page reads its MahaRERA record and the agents\' price sheet', () => {
    const c = { name: 'Gera World of Joy', builder: 'Gera Developments', locality: 'Kharadi', rera_no: 'P52100011111', bhk_options: [2, 3],
      price_min: 9500000, updated_at: '2026-10-22T08:00:00Z',
      rera: { regno: 'P52100011111', completion_now: '2028-06-30', completion_at_registration: '2028-06-30', units_total: 300, units_booked: 120, checked_at: '2026-10-19' } } as unknown as CatalogProject
    expect(catalogAnswer(c)).toBe('As of 19 Oct 2026, Gera World of Joy by Gera Developments in Kharadi, Pune is registered with MahaRERA as '
      + "P52100011111. The completion date filed with MahaRERA is 30 Jun 2028, not moved since registration. MahaRERA shows 120 of 300 homes booked. "
      + "2 & 3 BHK from ₹95 L on the agent's price sheet.")
    expect(projectUpdated(c)).toBe('2026-10-22')
    expect(projectUpdated(P)).toBe('2026-10-21')
    expect(projectUpdated({ ...P, page_updated: null })).toBeNull()
  })
})

// Park Eden Phase I (2026-10-25): MahaRERA's blanket order moved the date 4 months; the page said "moved from", as if the builder had
const EXT: RegisterProject = { ...P, completion_at_registration: '2030-10-31', completion_now: '2031-02-28', units_total: 249, units_booked: 27 }
const EXT_SENTENCE = "The completion date filed with MahaRERA is 28 Feb 2031; MahaRERA's August 2026 order added 4 months to it (the builder has not moved it)."

describe("the answer when the only change is MahaRERA's 2026 extension", () => {
  it('says the order added the months, never that the date moved, when the backend says extension_only', () => {
    const a = registerAnswer({ ...EXT, extension_only: true, details: { extension_months: 4 } as never })
    expect(a).toContain(EXT_SENTENCE)
    expect(a).not.toMatch(/moved from|increase|pushed/)
  })

  it('works it out from the dates when extension_only is absent: they differ by exactly the extension', () => {
    const a = registerAnswer({ ...EXT, details: { extension_months: 4 } as never })
    expect(a).toContain(EXT_SENTENCE)
    expect(a).not.toMatch(/moved from/)
  })

  it('keeps "moved from" for a real move, even with the extension inside it, and when the backend says it is not extension only', () => {
    expect(registerAnswer({ ...EXT, completion_now: '2031-06-30', details: { extension_months: 4 } as never }))
      .toContain('moved from 31 Oct 2030 at registration')
    expect(registerAnswer({ ...EXT, extension_only: false, details: { extension_months: 4 } as never })).toContain('moved from 31 Oct 2030')
  })

  it('reads bookings as "27 of 249 homes booked", never as homes available', () => {
    const a = registerAnswer(EXT)
    expect(a).toContain('MahaRERA shows 27 of 249 homes booked.')
    expect(a).not.toMatch(/available/)
  })
})

describe('an "All homes" price row', () => {
  const src = [{ site: 'parkeden.example', url: 'https://parkeden.example' }]
  const allHomes = { read_at: '2026-10-20', rows: [{ bhk: 'All homes', from_inr: 19_900_000, to_inr: null, official: true, sources: src }] }

  it('reads "Homes from ₹1.99 Cr", never "All homes BHK"', () => {
    const asked = askedPrices({ prices: allHomes })!
    expect(asked.bhks).toBe('')
    expect(asked.rows[0].text).toBe('Homes from ₹1.99 Cr')
    const a = registerAnswer({ ...P, prices: allHomes })
    expect(a).toContain('Homes from ₹1.99 Cr, as listed on parkeden.example on 20 Oct 2026.')
    expect(a).not.toMatch(/BHK/)
    expect(projectFaq({ ...P, prices: allHomes })[0].a).toMatch(/^Homes from ₹1.99 Cr, as listed/)
  })

  it('names only the BHK rows when sizes sit beside it', () => {
    const asked = askedPrices({ prices: { ...allHomes, rows: [...allHomes.rows,
      { bhk: '3 BHK', from_inr: 21_000_000, to_inr: 24_000_000, official: true, sources: src },
      { bhk: '4 BHK', from_inr: 30_000_000, to_inr: null, official: true, sources: src }] } })!
    expect(asked.bhks).toBe('3, 4 BHK')
    expect(asked.rows.map((r) => r.text)).toEqual(['Homes from ₹1.99 Cr', '3 BHK: ₹2.1 Cr to ₹2.4 Cr', '4 BHK: ₹3 Cr'])
  })
})

describe('filed dates and names', () => {
  it('counts whole months, keeping a month end a month end, and none for days that do not line up', () => {
    expect(monthsApart('2030-10-31', '2031-02-28')).toBe(4)
    expect(monthsApart('2029-06-30', '2029-10-30')).toBe(4)
    expect(monthsApart('2029-06-15', '2029-10-25')).toBeNull()
    expect(monthsApart(null, '2029-10-25')).toBeNull()
  })

  it('tells the extension from a move, and the change is "unknown" without the first date', () => {
    expect(completionChange({ ...EXT, details: { extension_months: 4 } as never })).toEqual({ kind: 'extension', from: '2030-10-31', months: 4 })
    expect(completionChange({ ...EXT, extension_only: true })).toEqual({ kind: 'extension', from: '2030-10-31', months: 4 })
    expect(completionChange(P)).toEqual({ kind: 'moved', from: '2028-12-31', extension: null })
    expect(completionChange({ ...P, completion_at_registration: null })).toEqual({ kind: 'unknown' })
    expect(completionChange({ ...P, completion_now: null })).toBeNull()
  })

  it("gives the heading the phase MahaRERA's name carries", () => {
    expect(headingName({ name: 'PARK EDEN PHASE I', marketed_name: 'Park Eden' })).toBe('Park Eden Phase I')
    expect(headingName({ name: 'Kolte Patil Life Republic Ph-2', marketed_name: 'Life Republic' })).toBe('Life Republic Phase 2')
    expect(headingName({ name: 'Park Eden Phase I', marketed_name: 'Park Eden Phase 1' })).toBe('Park Eden Phase 1')
    expect(headingName({ name: 'Gera World of Joy M', marketed_name: 'Gera World of Joy' })).toBe('Gera World of Joy')
  })

  it('the FAQ says the extension the same way', () => {
    const faq = projectFaq({ ...EXT, details: { extension_months: 4 } as never })
    expect(faq.find((f) => /possession date/.test(f.q))!.a).toContain(EXT_SENTENCE)
  })
})
