// What search engines read about a register project page (docs/plan/project-page-v2.md, "SEO"): the title leads with how people
// search for the project and its price, the description with the facts, and the structured data says only what the page shows.
import { render } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { offerPrice } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'
import { priceRowBhks, registerDescription, registerProjectJsonLd, registerTitle } from '@/lib/site/projectSeo'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <section id="enquire" /> }))

const SITE = 'https://avasetu.in'
const src = [{ site: 'parkeden.example', url: 'https://parkeden.example' }]

const EDEN: RegisterProject = {
  slug: 'park-eden-phase-i-kharadi', name: 'PARK EDEN PHASE I', marketed_name: 'Park Eden', aliases: ['Park Eden Kharadi Phase 1'],
  regno: 'P52100054321', promoter: 'Eden Realty LLP', pincode: '411014', area: { key: 'kharadi', slug: 'kharadi', name: 'Kharadi' },
  completion_now: '2031-02-28', completion_at_registration: '2030-10-31', units_total: 249, units_booked: 27,
  details_read_at: '2026-10-20', listed_or_updated: '2026-10-18', maharera_url: 'https://maharera.example/54321',
  paragraph: 'Park Eden is a project in Kharadi.', indexable: true, same_area: [], source: 'MahaRERA public records',
  map: { lat: 18.5512, lon: 73.9442 }, page_updated: '2026-10-24',
  profile: { read_at: '2026-10-20', highlights: [], plans: [], photos: [
    { url: '/uploads/eden/1.jpg', width: 1200, height: 800, alt: 'Park Eden towers', site: 'parkeden.example', page_url: null, source: 'builder' }] },
  prices: { read_at: '2026-10-21', rows: [
    { bhk: '3 BHK', from_inr: 21_500_000, to_inr: null, official: true, sqft: 1310, sources: src },
    { bhk: '4 BHK', from_inr: 29_000_000, to_inr: 32_000_000, official: true, sqft: 1720, sources: src },
    { bhk: 'All homes', from_inr: 19_900_000, to_inr: null, official: false, sources: src }] },
}

const BARE: RegisterProject = {
  slug: 'sai-heights-wagholi', name: 'Sai Heights', regno: 'P52100099999', promoter: null, pincode: null,
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: null, completion_at_registration: null,
  units_total: null, units_booked: null, details_read_at: null, listed_or_updated: null, maharera_url: null,
  paragraph: '', indexable: false, same_area: [], source: 'MahaRERA public records',
}

const byType = (lds: Record<string, unknown>[], t: string) => lds.find((x) => x['@type'] === t) as Record<string, any> | undefined

describe('register project title', () => {
  // EDEN: 27 of 249 homes booked, 10%
  it('leads with the name and area, then the price, the possession month and the share booked', () => {
    expect(registerTitle(EDEN)).toBe('Park Eden Kharadi: from ₹1.99 Cr, possession Feb 2031, 10% booked')
  })

  it('keeps the share booked before the BHK sizes, and the sizes before ", Pune"', () => {
    const unbooked = { ...EDEN, units_booked: 0 }
    expect(registerTitle(unbooked)).toBe('Park Eden Kharadi: 3 & 4 BHK from ₹1.99 Cr, possession Feb 2031')
  })

  it('adds ", Pune" when there is room', () => {
    const short = { ...EDEN, marketed_name: 'Eden', units_booked: 0, prices: null }
    expect(registerTitle(short)).toBe('Eden Kharadi, Pune: possession Feb 2031')
  })

  it('leads with how people search for it, without saying the area twice', () => {
    expect(registerTitle({ ...EDEN, search_name: 'Park Eden Kharadi' })).toBe('Park Eden Kharadi: from ₹1.99 Cr, possession Feb 2031, 10% booked')
  })

  it('an "All homes" row gives a price but no size', () => {
    const only = { ...EDEN, units_booked: 0, prices: { read_at: null, rows: [EDEN.prices!.rows[2]] } }
    expect(priceRowBhks(only)).toBe('')
    expect(registerTitle(only)).toBe('Park Eden Kharadi, Pune: from ₹1.99 Cr, possession Feb 2031')
  })

  it("quotes the agent's sheet over the asked prices", () => {
    const offer = { price_inr: 18_500_000, homes: [{ bhk: 3, label: '3 BHK', price_inr: 18_500_000 }, { bhk: 4, label: '4 BHK', price_inr: 26_000_000 }] }
    expect(registerTitle({ ...EDEN, units_booked: 0 }, offerPrice(offer))).toBe('Park Eden Kharadi: 3 & 4 BHK from ₹1.85 Cr, possession Feb 2031')
  })

  it('drops whole parts for a long name and keeps the price longest', () => {
    const long = { ...EDEN, marketed_name: 'Park Eden Grand Residences Signature' }
    expect(registerTitle(long)).toBe('Park Eden Grand Residences Signature Kharadi, Pune: from ₹1.99 Cr')
    const longer = { ...EDEN, marketed_name: 'Park Eden Grand Residences Signature Collection' }
    expect(registerTitle(longer)).toBe('Park Eden Grand Residences Signature Collection: from ₹1.99 Cr')
    for (const t of [registerTitle(long), registerTitle(longer)]) expect(t.length).toBeLessThanOrEqual(65)
  })

  it('says the MahaRERA number only when there is nothing else to say', () => {
    expect(registerTitle({ ...EDEN, prices: null })).toBe('Park Eden Kharadi, Pune: possession Feb 2031, 10% booked')
    expect(registerTitle(BARE)).toBe('Sai Heights Wagholi, Pune: MahaRERA P52100099999')
  })

  it('never says 100% before every home is booked', () => {
    expect(registerTitle({ ...EDEN, prices: null, units_booked: 248 })).toContain('99% booked')
    expect(registerTitle({ ...EDEN, prices: null, units_booked: 249 })).toContain('100% booked')
  })

  it("says the whole project's share, and none when a registration does not report bookings", () => {
    const towers = [
      { regno: 'P1', name: 'Park Eden Phase 1', completion_now: '2031-02-28', completion_at_registration: null, units_total: 249, units_booked: 27, registered_on: null, maharera_url: null },
      { regno: 'P2', name: 'Park Eden Phase 2', completion_now: '2032-06-30', completion_at_registration: null, units_total: 251, units_booked: 223, registered_on: null, maharera_url: null },
    ]
    const project = { registrations: 2, regnos: ['P1', 'P2'], units_total: 500, units_counted: 2, units_booked: 250, booked_of: 500, booked_counted: 2,
      completion_first: '2031-02-28', completion_last: '2032-06-30', completion_passed: false }
    const two = { ...EDEN, prices: null, towers, project }
    // the share booked goes before the phases when both do not fit
    expect(registerTitle(two)).toBe('Park Eden Kharadi, Pune: possession from Feb 2031, 50% booked')
    expect(registerTitle({ ...two, project: { ...project, booked_counted: 1 } })).toBe('Park Eden Phase 1 & 2, Kharadi, Pune: possession from Feb 2031')
  })

  it('names the phases only when every registration is a phase and the name does not say one', () => {
    const t = (name: string) => ({ regno: name, name, completion_now: null, completion_at_registration: null, units_total: null, units_booked: null, registered_on: null, maharera_url: null })
    const p = { ...BARE, towers: [t('Sai Heights Phase I'), t('Sai Heights Phase II')] }
    expect(registerTitle(p)).toBe('Sai Heights Phase I & II, Wagholi, Pune: MahaRERA P52100099999')
    expect(registerTitle({ ...p, towers: [t('Sai Heights Phase I'), t('Sai Heights Tower B')] })).toBe('Sai Heights Wagholi, Pune: MahaRERA P52100099999')
    expect(registerTitle({ ...p, marketed_name: 'Sai Heights Phase 2' })).toMatch(/^Sai Heights Phase 2 Wagholi/)
  })

  it("writes a name MahaRERA shouts in normal case, keeping a builder's initials", () => {
    expect(registerTitle({ ...BARE, name: 'MANSHA PHASE-II' })).toMatch(/^Mansha Phase-II Wagholi/)
    expect(registerTitle({ ...BARE, name: 'SSP AMALTAS ENCLAVE' })).toMatch(/^SSP Amaltas Enclave Wagholi/)
  })
})

describe('register project description', () => {
  it('says the sizes, price, possession, bookings and the check', () => {
    const d = registerDescription(EDEN)
    // the builder goes first to fit Google's 160 characters; the sizes, price, possession, bookings and the check stay
    expect(d).toBe('Park Eden, Kharadi, Pune: 3 & 4 BHK, 1,310–1,720 sq ft, from ₹1.99 Cr. Possession Feb 2031, 27 of 249 homes booked. MahaRERA P52100054321, checked by Avasetu.')
    expect(d.length).toBeLessThanOrEqual(160)
  })

  it("uses the page doctor's description when it has one", () => {
    const doctor = 'Park Eden Kharadi: 3 and 4 BHK from ₹1.99 Cr, possession Feb 2031 on MahaRERA, 27 of 249 homes booked.'
    expect(registerDescription({ ...EDEN, search_description: doctor })).toBe(doctor)
    expect(registerDescription({ ...BARE, search_description: 'Sai Heights in Wagholi, on MahaRERA.' })).toBe('Sai Heights in Wagholi, on MahaRERA.')
  })

  it('keeps the facts when the page quotes a price the doctor did not', () => {
    expect(registerDescription({ ...EDEN, search_description: 'Park Eden in Kharadi, on MahaRERA.' })).toMatch(/^Park Eden, Kharadi, Pune: 3 & 4 BHK.* from ₹1.99 Cr\./)
  })

  it('a bare record still says where it is and that we checked it', () => {
    expect(registerDescription(BARE)).toBe('Sai Heights, Wagholi, Pune. MahaRERA P52100099999, checked by Avasetu.')
  })
})

describe('register project structured data', () => {
  it('describes the complex with its address, map, homes, pictures, builder and an offer per priced size', () => {
    const lds = registerProjectJsonLd({ p: EDEN, siteUrl: SITE, photos: EDEN.profile!.photos, updated: '2026-10-24',
      faq: [{ q: 'What is the price of Park Eden?', a: 'From ₹1.99 Cr.' }] })
    expect(lds.map((x) => x['@type'])).toEqual(['ApartmentComplex', 'BreadcrumbList', 'FAQPage', 'WebPage'])
    const c = byType(lds, 'ApartmentComplex')!
    expect(c.name).toBe('Park Eden')
    expect(c.url).toBe(`${SITE}/projects/park-eden-phase-i-kharadi`)
    expect(c.alternateName).toEqual(['Park Eden Kharadi Phase 1', 'PARK EDEN PHASE I'])
    expect(c.address).toEqual({ '@type': 'PostalAddress', addressLocality: 'Kharadi, Pune', addressRegion: 'Maharashtra', postalCode: '411014', addressCountry: 'IN' })
    expect(c.geo).toEqual({ '@type': 'GeoCoordinates', latitude: 18.5512, longitude: 73.9442 })
    expect(c.numberOfAccommodationUnits).toBe(249)
    expect(c.image).toEqual([`${SITE}/uploads/eden/1.jpg`])
    expect(c.builder).toEqual({ '@type': 'Organization', name: 'Eden Realty LLP' })
    expect(c.identifier).toEqual({ '@type': 'PropertyValue', propertyID: 'MahaRERA registration', value: 'P52100054321' })
    expect(c.offers).toEqual([
      { '@type': 'Offer', name: '3 BHK at Park Eden', price: 21_500_000, priceCurrency: 'INR', validFrom: '2026-10-21',
        itemOffered: { '@type': 'Apartment', name: '3 BHK at Park Eden', floorSize: { '@type': 'QuantitativeValue', value: 1310, unitCode: 'FTK' } } },
      { '@type': 'AggregateOffer', name: '4 BHK at Park Eden', lowPrice: 29_000_000, highPrice: 32_000_000, priceCurrency: 'INR', validFrom: '2026-10-21',
        itemOffered: { '@type': 'Apartment', name: '4 BHK at Park Eden', floorSize: { '@type': 'QuantitativeValue', value: 1720, unitCode: 'FTK' } } },
      { '@type': 'Offer', name: 'Homes at Park Eden', price: 19_900_000, priceCurrency: 'INR', validFrom: '2026-10-21',
        itemOffered: { '@type': 'Apartment', name: 'Homes at Park Eden' } },
    ])
    expect(byType(lds, 'BreadcrumbList')!.itemListElement.map((i: { name: string; item: string }) => [i.name, i.item])).toEqual([
      ['Home', SITE], ['Projects', `${SITE}/projects`], ['Kharadi', `${SITE}/localities/kharadi`], ['Park Eden', `${SITE}/projects/park-eden-phase-i-kharadi`]])
    expect(byType(lds, 'FAQPage')!.mainEntity[0]).toEqual({ '@type': 'Question', name: 'What is the price of Park Eden?', acceptedAnswer: { '@type': 'Answer', text: 'From ₹1.99 Cr.' } })
    expect(byType(lds, 'WebPage')).toEqual({ '@context': 'https://schema.org', '@type': 'WebPage', url: c.url, name: 'Park Eden', dateModified: '2026-10-24' })
  })

  it("offers the agent's sheet, not the asked prices, when the page quotes it", () => {
    const offer = { price_inr: 18_500_000, homes: [{ bhk: 3, label: '3 BHK', carpet_sqft: 1290, price_inr: 18_500_000 }, { bhk: 4, label: '4 BHK', price_inr: 26_000_000 }] }
    const c = byType(registerProjectJsonLd({ p: EDEN, siteUrl: SITE, offer }), 'ApartmentComplex')!
    expect(c.offers.map((o: { name: string; price: number }) => [o.name, o.price])).toEqual([['3 BHK at Park Eden', 18_500_000], ['4 BHK at Park Eden', 26_000_000]])
    expect(c.offers[0].itemOffered.floorSize.value).toBe(1290)
    expect(c.offers[1].itemOffered.floorSize).toBeUndefined()
  })

  it('a bare record states no empty facts', () => {
    const lds = registerProjectJsonLd({ p: BARE, siteUrl: SITE })
    expect(lds.map((x) => x['@type'])).toEqual(['ApartmentComplex', 'BreadcrumbList'])
    const c = byType(lds, 'ApartmentComplex')!
    expect(Object.keys(c).sort()).toEqual(['@context', '@type', 'address', 'description', 'identifier', 'name', 'url'])
    expect(c.address).toEqual({ '@type': 'PostalAddress', addressLocality: 'Wagholi, Pune', addressRegion: 'Maharashtra', addressCountry: 'IN' })
    expect(JSON.stringify(lds)).not.toMatch(/null|""|\[\]/)
  })

  it('the page renders exactly what the builder returns, one script each', () => {
    const { container } = render(<RegisterProjectPage p={EDEN} siteUrl={SITE} facts={null} />)
    const lds = [...container.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent || '{}'))
    expect(lds.filter((x) => x['@type'] === 'ApartmentComplex')).toHaveLength(1)
    expect(byType(lds, 'ApartmentComplex')!.offers).toHaveLength(3)
    expect(byType(lds, 'BreadcrumbList')).toBeDefined()
    expect(byType(lds, 'WebPage')!.dateModified).toBe('2026-10-24')
  })
})


describe('offices and shops', () => {
  const base = { slug: 'gateway-kharadi', name: 'Gateway', regno: 'P1', units_total: 29, towers: [] } as unknown as RegisterProject
  it('are a Place, not an ApartmentComplex, with no accommodation count', () => {
    const [ld] = registerProjectJsonLd({ p: { ...base, homes: false }, siteUrl: 'https://avasetu.in' }) as Record<string, unknown>[]
    expect(ld['@type']).toBe('Place')
    expect(ld.numberOfAccommodationUnits).toBeUndefined()
  })
  it('homes stay an ApartmentComplex', () => {
    const [ld] = registerProjectJsonLd({ p: { ...base, homes: true }, siteUrl: 'https://avasetu.in' }) as Record<string, unknown>[]
    expect(ld['@type']).toBe('ApartmentComplex')
  })
})

// The name and place the sites printing the MahaRERA number sell a project under (backend seo/marketname.py): "Altamira By VTP
// Luxe", pincode 412207 (Wagholi), is sold everywhere as "VTP Altamira" in Kharadi.
describe('a project sold under another name and place', () => {
  const ALTAMIRA: RegisterProject = {
    ...BARE, slug: 'altamira-by-vtp-luxe-phase-1-wagholi', name: 'ALTAMIRA BY VTP LUXE PHASE 1', marketed_name: 'Altamira By VTP Luxe',
    regno: 'P52100079807', pincode: '412207', completion_now: '2030-11-30',
    market_name: 'VTP Altamira', market_place: 'Kharadi', market_sites: 6,
    prices: { read_at: '2026-10-30', rows: [{ bhk: '3 BHK', from_inr: 14_000_000, to_inr: null, official: false, sqft: 989, sources: src }] },
  }

  it('leads the title with the market name and both places, theirs first', () => {
    expect(registerTitle(ALTAMIRA)).toBe('VTP Altamira Kharadi, Wagholi: from ₹1.4 Cr, possession Nov 2030')   // the sizes and Pune go first to fit 65
  })

  it('a name measured on our own searches still leads', () => {
    expect(registerTitle({ ...ALTAMIRA, search_name: 'Altamira Wagholi' })).toBe('Altamira Wagholi, Pune: 3 BHK from ₹1.4 Cr, possession Nov 2030')
  })

  it('keeps the legal name and says where it is sold as in the description', () => {
    const d = registerDescription(ALTAMIRA)
    expect(d).toContain('VTP Altamira')
    expect(d).toContain('Wagholi (sold as Kharadi)')
  })

  it('says on the page which place is which', () => {
    const { getByTestId } = render(<RegisterProjectPage p={ALTAMIRA} siteUrl={SITE} facts={null} />)
    expect(getByTestId('sold-as').textContent).toBe('Sold as Kharadi by 6 property sites; we list it under Wagholi (pincode 412207).')
  })

  it('says nothing of it when the sites agree with us', () => {
    const { queryByTestId } = render(<RegisterProjectPage p={{ ...ALTAMIRA, market_place: null }} siteUrl={SITE} facts={null} />)
    expect(queryByTestId('sold-as')).toBeNull()
    expect(registerTitle({ ...ALTAMIRA, market_place: null })).toBe('VTP Altamira Wagholi: 3 BHK from ₹1.4 Cr, possession Nov 2030')
  })
})
