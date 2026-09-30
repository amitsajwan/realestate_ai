/**
 * Locality pages: only stable, checkable statements. No prices per sq ft, no appreciation figures, no predictions.
 * Every transport statement points to an official source and says "approved is not running".
 */
export interface LocalityFaq { q: string; a: string }
export interface Locality {
  slug: string
  name: string
  /** Value used for matching listings (their `locality` field). */
  listingName: string
  tagline: string
  summary: string
  suits: string[]
  gettingAround: string[]
  checks: string[]
  faqs: LocalityFaq[]
  guides: string[] // insight slugs
  sources: { label: string; href: string }[]
  updated: string
  updatedLabel: string
}

const METRO_2B = { label: 'PIB: Pune Metro Phase-2, Corridor 2B (Ramwadi to Wagholi/Vitthalwadi)', href: 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2139488&reg=48&lang=2' }
const METRO_L4 = { label: 'PIB: Pune Metro Phase-2, Line 4 (Kharadi to Khadakwasla)', href: 'https://www.pmindia.gov.in/en/news_updates/cabinet-approves-pune-metro-rail-project-phase-2-kharadi-khadakwasla-line-4-nal-stop-warje-manik-baug-line-4a/' }
const RERA = { label: 'MahaRERA (official portal)', href: 'https://maharera.maharashtra.gov.in/' }

const COMMON_CHECKS = [
  'RERA registration number of the project, looked up on the MahaRERA website',
  'Carpet area in the agreement, and the price per sq ft of carpet area',
  'Where the water comes from, and what the power backup covers',
  'Possession date in the agreement compared with the one on the RERA page',
  'The full cost: stamp duty, registration, GST where applicable, parking and maintenance deposit',
]

export const LOCALITIES: Locality[] = [
  {
    slug: 'kharadi', name: 'Kharadi', listingName: 'Kharadi',
    tagline: 'Close to the big office campuses',
    summary: 'Kharadi is one of east Pune\'s main office areas, home to large campuses such as EON IT Park and World Trade Center Pune. It is an established neighbourhood, so it is usually the busiest and most expensive of the three areas on this corridor.',
    suits: ['Professionals who want a short trip to work', 'Buyers who prefer an established area with more existing services', 'Buyers with a comfortable budget who value time over space'],
    gettingAround: [
      'Roads around the office campuses are busy at rush hour: try your own commute at 9:00 am and 6:30 pm on a weekday before you decide.',
      'Metro Line 4 (Kharadi to Khadakwasla) has been approved by the Union Cabinet. Approved is not the same as running: check the current status on the Maha-Metro website and do not pay extra for a station that does not exist yet.',
    ],
    checks: COMMON_CHECKS,
    faqs: [
      { q: 'Is the metro running in Kharadi?', a: 'Not yet. Line 4 (Kharadi to Khadakwasla) is approved, which is different from running. Check the latest status on the official Maha-Metro website.' },
      { q: 'How do I compare two flats in Kharadi fairly?', a: 'Compare the price per sq ft of carpet area, not the headline price, and ask for the full cost sheet including parking, maintenance deposit, stamp duty and registration.' },
      { q: 'Should I buy ready-to-move or under construction?', a: 'Ready-to-move lets you see exactly what you buy. Under construction can cost less to enter but you wait and rely on the builder keeping the date, so check the RERA possession date and visit a finished project by the same builder.' },
    ],
    guides: ['kharadi-upper-kharadi-wagholi', 'metro-kharadi-wagholi-approved-not-running', 'site-visit-checklist-upper-kharadi-wagholi'],
    sources: [METRO_L4, RERA],
    updated: '2026-09-30', updatedLabel: '30 September 2026',
  },
  {
    slug: 'upper-kharadi', name: 'Upper Kharadi', listingName: 'Upper Kharadi',
    tagline: 'Newer projects, a short hop from Kharadi',
    summary: 'Upper Kharadi sits on the same eastern corridor as Kharadi and Wagholi. Many projects here are newer or still being built, so the quality of the builder and the accuracy of the possession date matter more than the brochure.',
    suits: ['Buyers who want newer towers and open space without going as far out as Wagholi', 'Buyers who can accept a short drive to the Kharadi offices', 'Buyers comfortable checking RERA details and visiting finished projects'],
    gettingAround: [
      'Test the road access at rush hour, not on a Sunday: the approaches to the main roads decide your daily commute.',
      'Two metro projects have been approved for this corridor (Line 4 from Kharadi and Corridor 2B towards Wagholi). Neither is a reason to pay extra today: approved lines take years to build.',
    ],
    checks: COMMON_CHECKS,
    faqs: [
      { q: 'What is the difference between Kharadi and Upper Kharadi?', a: 'Kharadi is closest to the office campuses and more established; Upper Kharadi tends to have newer projects and more open space. Visit both at rush hour before you choose.' },
      { q: 'How do I check an under-construction project?', a: 'Look up its RERA registration and stated possession date on MahaRERA, ask for the approved plan, and visit a finished project by the same builder.' },
      { q: 'What should I ask about water and power?', a: 'Ask whether water is municipal, tanker or borewell, how much storage the building has, and what the power backup covers (lifts, common areas, your flat) and who pays.' },
    ],
    guides: ['kharadi-upper-kharadi-wagholi', 'site-visit-checklist-upper-kharadi-wagholi'],
    sources: [METRO_L4, METRO_2B, RERA],
    updated: '2026-09-30', updatedLabel: '30 September 2026',
  },
  {
    slug: 'wagholi', name: 'Wagholi', listingName: 'Wagholi',
    tagline: 'Often more space for the budget, longer commute',
    summary: 'Wagholi is further out on the eastern corridor. Buyers often find more space for their budget and many newer towers, in exchange for a longer commute that depends on the road and the time of day.',
    suits: ['Buyers who want more space for their budget', 'Buyers who can live with a longer commute, or work from home some days', 'Buyers who do not mind waiting for future transport'],
    gettingAround: [
      'Corridor 2B of Pune Metro Phase-2 (Ramwadi to Wagholi/Vitthalwadi, about 11.6 km with 11 stations) has been approved by the Union Cabinet. Approved is not running: check progress on the official Maha-Metro website.',
      'Do the real commute test at 9:00 am and 6:30 pm on a weekday before you book.',
    ],
    checks: COMMON_CHECKS,
    faqs: [
      { q: 'Is there a metro to Wagholi?', a: 'Corridor 2B (Ramwadi to Wagholi/Vitthalwadi) is approved. It is not running yet, so do not pay extra for it today and check the latest status with Maha-Metro.' },
      { q: 'Is Wagholi cheaper than Kharadi?', a: 'Buyers often find more space for the budget in Wagholi, but prices depend on the project, tower and floor. Compare on carpet area and the full cost sheet rather than on the area name.' },
      { q: 'How far is Wagholi from the Kharadi offices?', a: 'It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.' },
    ],
    guides: ['kharadi-upper-kharadi-wagholi', 'metro-kharadi-wagholi-approved-not-running', 'site-visit-checklist-upper-kharadi-wagholi'],
    sources: [METRO_2B, RERA],
    updated: '2026-09-30', updatedLabel: '30 September 2026',
  },
]

export function getLocality(slug: string): Locality | undefined {
  return LOCALITIES.find((l) => l.slug === slug)
}
