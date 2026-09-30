/** Insights: buying guides for Pune. General information with cited official sources; no prices per sq ft, no predictions. */
export interface InsightSection {
  heading: string
  paragraphs?: string[]
  bullets?: string[]
}
export interface InsightSource { label: string; href: string }
export interface Insight {
  slug: string
  title: string
  summary: string
  updated: string // ISO date
  updatedLabel: string
  sections: InsightSection[]
  sources: InsightSource[]
}

const NOTE =
  'Government approvals and project status change, so check the sources before you decide. This is general information, not investment or legal advice.'
export const INSIGHT_NOTE = NOTE

export const INSIGHTS: Insight[] = [
  {
    slug: 'kharadi-upper-kharadi-wagholi',
    title: 'Kharadi, Upper Kharadi or Wagholi? How to choose in 10 minutes',
    summary: 'Three neighbourhoods on one corridor, very different daily lives. A quick way to decide where to spend your weekends viewing flats.',
    updated: '2026-09-30',
    updatedLabel: '30 September 2026',
    sections: [
      {
        heading: 'The one-line version',
        bullets: [
          'Kharadi: closest to the big office campuses. Established and busier, usually the priciest of the three.',
          'Upper Kharadi: the middle path. Newer projects and more open space, a short hop from Kharadi.',
          'Wagholi: often more space for the budget and newer towns, but a longer commute that depends on the road you take.',
        ],
        paragraphs: ['We do not quote prices per sq ft here: they differ by project, tower, floor and year, and they change. Ask for the full cost sheet and compare on carpet area.'],
      },
      {
        heading: 'Your commute decides more than you think',
        paragraphs: [
          'Kharadi is home to large office campuses such as EON IT Park and World Trade Center Pune, so living nearby can mean a short trip. Wagholi is further out.',
          'Do the real test: travel from the flat to your office at 9:00 am and again at 6:30 pm on a weekday, not on a Sunday.',
        ],
      },
      {
        heading: 'Metro: approved is not the same as running',
        paragraphs: [
          'The Union Cabinet has approved Pune Metro Phase-2, including Corridor 2B (Ramwadi to Wagholi/Vitthalwadi, about 11.6 km with 11 stations) and Line 4 (Kharadi to Khadakwasla). That is good news for this corridor, but an approved line takes years to build.',
          'Do not pay extra today for a metro that is not yet running. Check the latest status on the official Maha-Metro website.',
        ],
      },
      {
        heading: 'Ready-to-move or under construction',
        paragraphs: [
          'Wagholi and Upper Kharadi have many projects still being built. Under construction can mean a lower entry price, but you wait, and you rely on the builder keeping the promised date. Ready-to-move means you see exactly what you buy. Decide which risk you prefer.',
        ],
      },
      {
        heading: 'Five checks before you book anything',
        bullets: [
          'RERA registration of the project, and its stated possession date, on the MahaRERA website.',
          'Carpet area in the agreement, and the price per sq ft of carpet area, so you can compare fairly.',
          'Title and approvals: get a lawyer to check them.',
          "Possession date and the builder's earlier projects: visit one that is finished.",
          'The full cost: stamp duty, registration, GST where applicable, parking and maintenance deposit.',
        ],
      },
      {
        heading: 'So which one?',
        bullets: [
          'Choose Kharadi if a short commute matters most and your budget is comfortable.',
          'Choose Upper Kharadi if you want newer towers and open space without going as far as Wagholi.',
          'Choose Wagholi if you want more space for your budget and can live with the commute and the wait for the metro.',
        ],
      },
    ],
    sources: [
      { label: 'PIB: Pune Metro Phase-2, Corridor 2B (Ramwadi to Wagholi/Vitthalwadi)', href: 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2139488&reg=48&lang=2' },
      { label: 'PIB: Pune Metro Phase-2, Line 4 (Kharadi to Khadakwasla)', href: 'https://www.pmindia.gov.in/en/news_updates/cabinet-approves-pune-metro-rail-project-phase-2-kharadi-khadakwasla-line-4-nal-stop-warje-manik-baug-line-4a/' },
    ],
  },
  {
    slug: 'metro-kharadi-wagholi-approved-not-running',
    title: 'Metro near Kharadi and Wagholi: approved is not the same as running',
    summary: 'What has been approved, what it means for buyers today, and what not to pay extra for.',
    updated: '2026-09-30',
    updatedLabel: '30 September 2026',
    sections: [
      {
        heading: 'What has been approved',
        bullets: [
          'Corridor 2B: Ramwadi to Wagholi/Vitthalwadi, an elevated extension of the existing line (about 11.6 km, 11 stations).',
          'Line 4: Kharadi to Khadakwasla.',
        ],
        paragraphs: ['Both were approved by the Union Cabinet under Pune Metro Phase-2. See the official announcements linked below.'],
      },
      {
        heading: 'What it means for you today',
        paragraphs: [
          'Approval is a real milestone, but construction takes years and timelines can slip. A metro that is not running cannot shorten your commute yet.',
        ],
        bullets: [
          'Do not pay extra for a flat only because a station is planned nearby.',
          'Ask the seller how far the flat is from the planned alignment, then check the alignment yourself on the official Maha-Metro site.',
          'Judge the flat on how you would live in it if the metro arrives late.',
        ],
      },
      {
        heading: 'How to check the latest status',
        paragraphs: ['Look up the corridor on the Maha-Metro website and in recent news from the Cabinet approval onwards. Note the date of every source you rely on.'],
      },
    ],
    sources: [
      { label: 'PIB: Pune Metro Phase-2, Corridor 2B', href: 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2139488&reg=48&lang=2' },
      { label: 'PIB: Pune Metro Phase-2, Line 4', href: 'https://www.pmindia.gov.in/en/news_updates/cabinet-approves-pune-metro-rail-project-phase-2-kharadi-khadakwasla-line-4-nal-stop-warje-manik-baug-line-4a/' },
    ],
  },
  {
    slug: 'site-visit-checklist-upper-kharadi-wagholi',
    title: 'Site visit checklist for Upper Kharadi and Wagholi: 6 things to check',
    summary: 'A practical list to carry to your next site visit, so you judge the home and not the brochure.',
    updated: '2026-09-30',
    updatedLabel: '30 September 2026',
    sections: [
      {
        heading: 'Before you go',
        bullets: ['Ask for the RERA registration number and look it up on the MahaRERA website.', 'Ask for the full cost sheet: price, parking, maintenance deposit, stamp duty and registration.'],
      },
      {
        heading: 'On site',
        bullets: [
          'Visit at 9:00 am and again around 6:30 pm on a weekday. Note the traffic on the road outside.',
          'Ask where the water comes from (municipal supply, tanker or borewell) and how much storage the building has.',
          'Ask about power backup: what it covers (lifts, common areas, your flat) and who pays.',
          'Look at the road and drainage outside the gate. If you can, visit after rain.',
          'Ask about parking and visitor parking, and what the monthly maintenance covers.',
          'Visit a finished project by the same builder and speak to a resident.',
        ],
      },
      {
        heading: 'Before you pay a booking amount',
        paragraphs: ['Have a lawyer check the title and approvals, and compare the possession date in the agreement with the one on the RERA page.'],
      },
    ],
    sources: [{ label: 'MahaRERA (official portal)', href: 'https://maharera.maharashtra.gov.in/' }],
  },
]

export function getInsight(slug: string): Insight | undefined {
  return INSIGHTS.find((i) => i.slug === slug)
}
