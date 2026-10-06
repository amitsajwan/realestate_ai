/**
 * Locality pages: only stable, checkable statements. No prices per sq ft, no appreciation figures, no predictions.
 * Every transport statement points to an official source and says "approved is not running".
 * Areas, slugs, names and tiers mirror backend/app/core/areas.py (backend/tests/modules/knowledge/test_areas.py keeps them equal).
 * Where we could not find an official source (e.g. roads in Keshav Nagar) the page says so instead of guessing.
 */
export interface LocalityFaq { q: string; a: string }
/** Who an area mostly serves; mirrors `tier` in backend/app/core/areas.py (a backend test keeps them equal). */
export type LocalityTier = 'affordable' | 'it'
export const TIER_LABELS: Record<LocalityTier, { title: string; blurb: string }> = {
  affordable: { title: 'Affordable homes', blurb: 'Where many first-home and budget buyers look.' },
  it: { title: 'IT corridor', blurb: 'Around the Kharadi and Hinjawadi office campuses, and along Metro Line 3.' },
}

export interface Locality {
  slug: string
  /** Stable id from backend/app/core/areas.py ("keshav_nagar"); also the lead source tag `locality_<key>`. */
  key: string
  name: string
  tier: LocalityTier
  /** Other spellings people type (lower case), from backend/app/core/areas.py. */
  aliases: string[]
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
const METRO_L3 = { label: 'PMRDA: Pune Metro Line 3 (Maan-Hinjawadi to Shivajinagar), overview and route map', href: 'https://www.pmrda.gov.in/en/pune-metro-line-3/maan-hinjawadi-shivajinagar-metro-line/' }
const PMRDA_SEP_2026 = { label: 'PMRDA press note, September 2026: Metro Line 3 safety approval for the Maan to Balewadi section', href: 'https://www.pmrda.gov.in/wp-content/uploads/2026/09/Expedite-Punes-Ring-Road-and-Metro-Projects-Deputy-Chief-Minister-Directs-PMRDA.pdf' }
const PMRDA_JUN_2026 = { label: 'PMRDA press note, June 2026: Metro Line 3 and pre-monsoon work in Hinjawadi IT Park', href: 'https://www.pmrda.gov.in/wp-content/uploads/2026/06/Metro-Line-3-First-Phase-To-Roll-Out-By-July-15.pdf' }
const AAI_PUNE = { label: 'Airports Authority of India: Pune Airport, Lohegaon (fact sheet)', href: 'https://www.aai.aero/en/node/2685' }
const PCMC_TP = { label: 'PCMC town planning: development plan maps (Wakad is in Sector 7)', href: 'https://www.pcmcindia.gov.in/TP_info.php' }

/** Line 3 status as PMRDA last stated it; every area page on the line repeats it word for word. */
const L3_STATUS = 'In September 2026 PMRDA said the Commissioner of Metro Railway Safety had approved the 13.20 km Maan to Balewadi section. Approved is not the same as running: check the current status on the PMRDA website before you count on a station.'
const BROCHURE_TRANSPORT = 'If a brochure mentions a new metro line or road, ask which official approval it refers to and check its status on the website of the agency building it: approved is not the same as running, and approved lines take years to build.'
const COMMUTE_TEST = 'We do not quote travel times. Try your own commute at 9:00 am and 6:30 pm on a weekday before you decide.'

const COMMON_CHECKS = [
  'RERA registration number of the project, looked up on the MahaRERA website',
  'Carpet area in the agreement, and the price per sq ft of carpet area',
  'Where the water comes from, and what the power backup covers',
  'Possession date in the agreement compared with the one on the RERA page',
  'The full cost: stamp duty, registration, GST where applicable, parking and maintenance deposit',
]

export const LOCALITIES: Locality[] = [
  {
    slug: 'kharadi', key: 'kharadi', name: 'Kharadi', tier: 'it', aliases: ['kharadi'], listingName: 'Kharadi',
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
    slug: 'upper-kharadi', key: 'upper_kharadi', name: 'Upper Kharadi', tier: 'affordable', aliases: ['upper kharadi', 'upper-kharadi'], listingName: 'Upper Kharadi',
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
    slug: 'wagholi', key: 'wagholi', name: 'Wagholi', tier: 'affordable', aliases: ['wagholi'], listingName: 'Wagholi',
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
  {
    slug: 'lohegaon', key: 'lohegaon', name: 'Lohegaon', tier: 'affordable', aliases: ['lohegaon', 'lohgaon'], listingName: 'Lohegaon',
    tagline: 'Where Pune airport is',
    summary: 'Lohegaon, in north-east Pune, is where Pune airport is: the Airports Authority of India runs the civil terminal as a civil enclave, and air traffic control is with the Indian Air Force. Many buyers here are looking for a first home, so the builder, the possession date and the full cost matter more than the brochure.',
    suits: ['People who fly often and want to live near the airport', 'First-home buyers ready to compare several projects on carpet area and the full cost sheet', 'Buyers comfortable checking RERA details and visiting finished projects by the same builder'],
    gettingAround: [
      COMMUTE_TEST,
      BROCHURE_TRANSPORT,
    ],
    checks: [
      ...COMMON_CHECKS,
      'Aircraft noise: visit the flat in the morning, the evening and once at night before you decide',
      'Whether the project needed a height clearance because of the airport, and a copy of it',
    ],
    faqs: [
      { q: 'Is Pune airport in Lohegaon?', a: 'Yes. The Airports Authority of India lists its civil enclave as Pune Airport, Lohegaon. Air traffic control there is with the Indian Air Force.' },
      { q: 'Will I hear the planes?', a: 'It depends on where the flat is and which way it faces. Visit at different times of day, including once at night, and listen for yourself before you book.' },
      { q: 'How do I check an under-construction project?', a: 'Look up its RERA registration and stated possession date on MahaRERA, ask for the approved plan, and visit a finished project by the same builder.' },
    ],
    guides: ['site-visit-checklist-upper-kharadi-wagholi'],
    sources: [AAI_PUNE, RERA],
    updated: '2026-10-04', updatedLabel: '4 October 2026',
  },
  {
    slug: 'keshav-nagar', key: 'keshav_nagar', name: 'Keshav Nagar', tier: 'affordable', aliases: ['keshav nagar', 'keshavnagar', 'keshav-nagar'], listingName: 'Keshav Nagar',
    tagline: 'Check each project on MahaRERA',
    summary: 'Keshav Nagar is a residential area in east Pune, in the Mundhwa area. We have not yet found official sources about its roads and transport that we can cite, so this page sticks to what you can check yourself and to the projects listed on MahaRERA.',
    suits: ['First-home buyers ready to compare several projects on carpet area and the full cost sheet', 'Buyers who will look up each project on MahaRERA before booking', 'Buyers who can test the commute themselves at rush hour'],
    gettingAround: [
      COMMUTE_TEST,
      BROCHURE_TRANSPORT,
    ],
    checks: COMMON_CHECKS,
    faqs: [
      { q: 'Is Keshav Nagar the same as Mundhwa?', a: 'Keshav Nagar is in the Mundhwa area, and the two names are often used together in addresses. Check the exact address and survey number in the agreement and on the MahaRERA page of the project.' },
      { q: 'How far is Keshav Nagar from the Kharadi offices?', a: 'It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.' },
      { q: 'How do I check an under-construction project?', a: 'Look up its RERA registration and stated possession date on MahaRERA, ask for the approved plan, and visit a finished project by the same builder.' },
    ],
    guides: ['site-visit-checklist-upper-kharadi-wagholi'],
    sources: [RERA],
    updated: '2026-10-04', updatedLabel: '4 October 2026',
  },
  {
    slug: 'hinjawadi', key: 'hinjawadi', name: 'Hinjawadi', tier: 'it', aliases: ['hinjawadi', 'hinjewadi'], listingName: 'Hinjawadi',
    tagline: 'Home of the Rajiv Gandhi IT Park',
    summary: 'Hinjawadi, on Pune\'s western edge, is home to the Rajiv Gandhi IT Park. PMRDA is building Pune Metro Line 3 from Maan-Hinjawadi to Shivajinagar to ease traffic in and around the IT park, so the daily commute and the roads in the monsoon matter as much as the flat.',
    suits: ['People who work in the Rajiv Gandhi IT Park and want a short trip to work', 'Buyers who will check the metro status themselves rather than pay extra for a station that is not open yet', 'Buyers comfortable checking RERA details and visiting finished projects by the same builder'],
    gettingAround: [
      'PMRDA is building Pune Metro Line 3 (Maan-Hinjawadi to Shivajinagar), an elevated line of about 23.2 km with 23 stations, as a public-private partnership. ' + L3_STATUS,
      'PMRDA itself names traffic congestion in the Maan-Hinjawadi area as the reason to finish Line 3. ' + COMMUTE_TEST,
      'Before the 2026 monsoon, PMRDA, MIDC and the local gram panchayats inspected the Hinjawadi IT Park to clear choke points and prevent waterlogging. Drive the approach roads after heavy rain before you book.',
    ],
    checks: [...COMMON_CHECKS, 'How the approach road to the building copes after heavy rain'],
    faqs: [
      { q: 'Is the metro running in Hinjawadi?', a: 'Check the current status on the PMRDA website. In September 2026 PMRDA said the Maan to Balewadi section of Line 3 had its safety approval; approved is not the same as running, so do not pay extra for a station until trains are carrying passengers.' },
      { q: 'Should I buy ready-to-move or under construction?', a: 'Ready-to-move lets you see exactly what you buy. Under construction can cost less to enter but you wait and rely on the builder keeping the date, so check the RERA possession date and visit a finished project by the same builder.' },
      { q: 'How far is Hinjawadi from the rest of Pune?', a: 'It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.' },
    ],
    guides: [],
    sources: [METRO_L3, PMRDA_SEP_2026, PMRDA_JUN_2026, RERA],
    updated: '2026-10-04', updatedLabel: '4 October 2026',
  },
  {
    slug: 'wakad', key: 'wakad', name: 'Wakad', tier: 'it', aliases: ['wakad'], listingName: 'Wakad',
    tagline: 'Between Hinjawadi and Balewadi, in PCMC',
    summary: 'Wakad lies between Hinjawadi and Balewadi and comes under the Pimpri Chinchwad Municipal Corporation (PCMC). On PMRDA\'s route map, Pune Metro Line 3 has a station at Wakad Chowk, between the Hinjawadi stations and Balewadi.',
    suits: ['People who work in Hinjawadi and want to live on the Line 3 route', 'Buyers who will check the metro status themselves rather than pay extra for a station that is not open yet', 'Buyers willing to look up a plot on PCMC\'s development plan maps before booking'],
    gettingAround: [
      'Pune Metro Line 3 (Maan-Hinjawadi to Shivajinagar) is being built by PMRDA, with a station at Wakad Chowk on its route map. ' + L3_STATUS,
      COMMUTE_TEST,
    ],
    checks: [...COMMON_CHECKS, 'The plot on PCMC\'s development plan maps (Wakad is in Sector 7 of the revised draft plan): planned roads and reservations next to the building'],
    faqs: [
      { q: 'Is there a metro station in Wakad?', a: 'PMRDA\'s route map for Line 3 shows a station at Wakad Chowk. In September 2026 PMRDA said the Maan to Balewadi section had its safety approval; approved is not the same as running, so check the current status on the PMRDA website.' },
      { q: 'Which civic body looks after Wakad?', a: 'Wakad comes under the Pimpri Chinchwad Municipal Corporation (PCMC). Its town planning page has the development plan maps for Wakad.' },
      { q: 'How far is Wakad from the Hinjawadi IT park?', a: 'It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.' },
    ],
    guides: [],
    sources: [METRO_L3, PMRDA_SEP_2026, PCMC_TP, RERA],
    updated: '2026-10-04', updatedLabel: '4 October 2026',
  },
  {
    slug: 'baner', key: 'baner', name: 'Baner', tier: 'it', aliases: ['baner'], listingName: 'Baner',
    tagline: 'On the Line 3 route to Shivajinagar',
    summary: 'Baner is in west Pune, on the route of Pune Metro Line 3 from Maan-Hinjawadi to Shivajinagar, which has stations named Baner Gaon and Baner on PMRDA\'s route map. The Baner ramp of PMRDA\'s double-decker flyover at Pune University opened to traffic on 8 March 2026.',
    suits: ['Buyers who want to live on the Line 3 route between Hinjawadi and Shivajinagar', 'Buyers who will check the metro status themselves rather than pay extra for a station that is not open yet', 'Buyers comfortable checking RERA details and visiting finished projects by the same builder'],
    gettingAround: [
      'Pune Metro Line 3 (Maan-Hinjawadi to Shivajinagar) is being built by PMRDA, with stations named Baner Gaon and Baner on its route map. ' + L3_STATUS,
      'PMRDA\'s double-decker flyover at Pune University: the Baner ramp and the lanes between Baner and Shivajinagar opened to traffic on 8 March 2026.',
      COMMUTE_TEST,
    ],
    checks: COMMON_CHECKS,
    faqs: [
      { q: 'Is the metro running in Baner?', a: 'The safety approval PMRDA announced in September 2026 was for the Maan to Balewadi section of Line 3; approved is not the same as running. Check the current status of the Baner stations on the PMRDA website.' },
      { q: 'How do I compare two flats in Baner fairly?', a: 'Compare the price per sq ft of carpet area, not the headline price, and ask for the full cost sheet including parking, maintenance deposit, stamp duty and registration.' },
      { q: 'How far is Baner from the Hinjawadi IT park?', a: 'It depends on the route and the time. We do not quote times here: try the trip yourself at rush hour before you decide.' },
    ],
    guides: [],
    sources: [METRO_L3, PMRDA_SEP_2026, RERA],
    updated: '2026-10-04', updatedLabel: '4 October 2026',
  },
]

export function getLocality(slug: string): Locality | undefined {
  return LOCALITIES.find((l) => l.slug === slug)
}

const TITLE_WORDS = new Set(['it'])

export function localityNameFromSlug(slug: string): string {
  return slug.split('-').filter(Boolean).map((w) => {
    const lower = w.toLowerCase()
    return TITLE_WORDS.has(lower) ? lower.toUpperCase() : lower.charAt(0).toUpperCase() + lower.slice(1)
  }).join(' ')
}

export function localitySlug(name: string | null | undefined): string {
  return (name || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80)
}

/** The area guide for a locality name as agents type it ("upper kharadi", "Upper Kharadi "), if we have one. */
export function localityByName(name: string | null | undefined): Locality | undefined {
  const want = (name || '').trim().toLowerCase().split(/\s+/).join(' ')
  return want ? LOCALITIES.find((l) => l.listingName.toLowerCase() === want || l.aliases.includes(want)) : undefined
}

/** Areas of one tier, in the order of the area list. */
export function localitiesByTier(tier: LocalityTier): Locality[] {
  return LOCALITIES.filter((l) => l.tier === tier)
}

/** The `?src=` tag an area page passes to the enquiry form, so the lead shows which area the buyer asked about. */
export function localitySource(l: Pick<Locality, 'key'>): string {
  return `locality_${l.key}`
}

export function localitySourceFromSlug(slug: string): string {
  return `locality_${slug.replace(/-/g, '_')}`.slice(0, 40)
}
