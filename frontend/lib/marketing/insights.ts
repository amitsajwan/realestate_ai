/** Insights: buying guides for Pune. General information with cited official sources; no prices per sq ft, no predictions. */
export interface InsightSource { label: string; href: string }
export interface InsightSection {
  heading: string
  paragraphs?: string[]
  bullets?: string[]
  /** pages to read next, after the text: our own pages ("/projects/...") or another site's */
  links?: InsightSource[]
}
export interface Insight {
  slug: string
  title: string
  summary: string
  updated: string // ISO date
  updatedLabel: string
  sections: InsightSection[]
  sources: InsightSource[]
  /** about how Avasetu works rather than a guide to buying, so agents' pages, which list buyer guides, leave it out */
  aboutUs?: boolean
}

const NOTE =
  'Government approvals and project status change, so check the sources before you decide. This is general information, not investment or legal advice.'
export const INSIGHT_NOTE = NOTE

export const INSIGHTS: Insight[] = [
  {
    slug: 'ai-real-estate-data-verification',
    title: 'How we use AI on Pune property pages without letting it make things up',
    summary:
      'AI can write about any Pune project, including things that are not true. How every Avasetu page starts from MahaRERA and checked sources, what AI may and may not do, and two live pages that show it: Kohinoor Kaleido in Wagholi and Venkatesh Vanaya in Kharadi.',
    updated: '2026-11-21',
    updatedLabel: '21 November 2026',
    aboutUs: true,
    sections: [
      {
        heading: 'The short version',
        bullets: [
          'Facts come first: the MahaRERA record, prices with their source and date, and a map pin checked against the registration. AI only puts checked facts into sentences.',
          'A fact found on one website alone stays off the page until another source confirms it.',
          'Every piece of AI writing is checked in code before it reaches a page. When a draft fails, the page shows the facts in plain sentences instead.',
          'Each page says where each fact came from and when it was last checked, including what is not checked yet.',
          "One registration's numbers are never passed off as a whole project's.",
        ],
      },
      {
        heading: 'Why AI on its own is risky on a property page',
        paragraphs: [
          "A language model is built to write the likely next sentence, not the true one. Asked about a Pune project, it will happily describe a swimming pool the project does not have, a price nobody quoted, or the possession date from last year's brochure. It reads well, and that is the danger: on a property page a confident mistake can cost a family lakhs.",
          'Much of what is written about projects online is copied from brochures and from other property sites, so even a careful model repeats their mistakes. We use AI as a writer, never as a source.',
        ],
      },
      {
        heading: 'Step 1: the register before the writing',
        paragraphs: [
          'Every project page starts from its MahaRERA registration: the registration number, the promoter, the pincode, the completion date the builder filed and every change to it, and how many homes are booked. We read the register again and again and keep every reading, which is how a page can say that a date moved or that bookings picked up.',
          "Prices come from the builder's own site, or from two property sites that agree, and each carries the date it was checked. A project's place comes from its map pin, checked against its MahaRERA name and pincode.",
        ],
      },
      {
        heading: 'Step 2: what AI may do, and what it may not',
        bullets: [
          'It may turn checked facts into readable sentences, such as the short notes under "What stands out" on a project page.',
          'It may read builder sites and brochures to find facts, which are used only when they agree with MahaRERA or a second source.',
          'It may not invent a fact, give a number without a source, describe offices or shops as homes, or place a project somewhere its MahaRERA record does not support.',
        ],
      },
      {
        heading: 'Step 3: every output is checked',
        paragraphs: [
          'Before AI writing reaches a page, code checks it: each number has to match a fact we hold, and claims we never make, such as promised returns, advert language or a fact no source backs, are refused. When a draft does not pass, the page does not wait for a better one. It shows the facts in plain sentences: less elegant, always true.',
          'Pages are read again after they go live, so a fact that has since changed on MahaRERA is caught and the page shows the new date.',
        ],
      },
      {
        heading: 'Example: Kohinoor Kaleido, Wagholi. Where is it, really?',
        paragraphs: [
          "Kohinoor Kaleido (MahaRERA P52100046027) is sold as a Kharadi project by five property sites. Its MahaRERA record gives the pincode 412207, which is Wagholi's, so its page lists it under Wagholi and says so in one line at the top. A model that learned from listings would have repeated \"Kharadi\".",
          "The page's sources panel shows where each part came from: the registration, dates and bookings from MahaRERA, prices from the builder's site or two property sites that agree, each with the date it was checked. On 21 November 2026 it also showed the description as \"Not checked yet\". Saying what is not checked is part of the job.",
        ],
        links: [{ label: 'Kohinoor Kaleido, Wagholi', href: '/projects/kohinoor-kaleido-wagholi' }],
      },
      {
        heading: 'Example: Venkatesh Vanaya, Kharadi. One registration is not the whole project',
        paragraphs: [
          "Venkatesh Vanaya is filed with MahaRERA as several registrations, one for each phase, and each has its own homes, bookings and completion date. Putting one phase's numbers in a headline would mislead, so the page gives the whole development's figures and says what they cover: on 20 November 2026, not one of 745 homes across 6 of its 7 registrations had been booked.",
          'The completion date shows why the history matters. The phase the page is built on has a completion date of 30 April 2031, after a MahaRERA order added months to the 31 December 2030 first filed. A brochure shows one date; the register shows how it got there. The page also shows satellite pictures of the site from November 2022 to April 2026, centred on the checked pin, so anyone can see how far work has gone.',
        ],
        links: [{ label: 'Venkatesh Vanaya, Kharadi', href: '/projects/venkatesh-vanaya-wing-i-j-phase-2-kharadi' }],
      },
      {
        heading: 'Where people still come in',
        paragraphs: [
          "Some facts only a person can confirm. A site visit note on a project page is written by our team, never by a model. When a reader tells us a page is wrong, we check it against MahaRERA and the builder's documents, fix it, and the page shows the new date.",
        ],
        links: [
          { label: 'How we check every project', href: '/about#how-we-check' },
          { label: 'Check any project against MahaRERA', href: '/check' },
          { label: 'Tell us a page is wrong', href: '/contact' },
        ],
      },
      {
        heading: 'Why it matters',
        paragraphs: [
          'Google and AI assistants increasingly answer property questions themselves, and they quote pages that state checked facts with their sources and dates. Being plainly correct is how a small Pune platform earns that trust, one project page at a time.',
        ],
      },
    ],
    sources: [
      { label: 'MahaRERA (official portal)', href: 'https://maharera.maharashtra.gov.in/' },
      { label: 'A shorter version of this article on LinkedIn', href: 'https://www.linkedin.com/pulse/how-we-use-ai-pune-real-estate-pages-without-letting-make-things-isxxf/' },
    ],
  },
  {
    slug: 'diwali-home-offers-pune-decoded',
    title: "Diwali home offers in Pune, decoded: what 'zero stamp duty' and 'no EMI' really cost",
    summary:
      'Festive offers are real money, but only if the price is not raised to pay for them. A worked example on a ₹75 lakh flat, and what to get in writing before you pay a booking amount.',
    updated: '2026-10-15',
    updatedLabel: '15 October 2026',
    sections: [
      {
        heading: 'The short version',
        bullets: [
          "Compare the full cost sheet with and without the offer. An offer is worth something only if the flat's price stays the same.",
          "'Zero stamp duty' can be worth several lakh in Pune city. Check that the agreement value is not quietly higher.",
          "'No EMI till possession' depends on the possession date holding. Ask what happens if it moves.",
          'Gold coins and free kitchens are worth what you would pay for them, not what the brochure says. A price cut is usually worth more.',
          'Under the RERA Act, a builder may not take more than 10% of the cost before a registered agreement for sale.',
        ],
      },
      {
        heading: 'First: what a flat costs on top of its price',
        paragraphs: [
          'An example, not a price we are quoting: a flat with an agreement value of ₹75 lakh in Pune Municipal Corporation limits (Kharadi and Wagholi are both inside them).',
        ],
        bullets: [
          'Stamp duty: about 7% in PMC and PCMC areas, or 6% when the home is registered only in a woman’s name. On ₹75 lakh, about ₹5.25 lakh (₹4.5 lakh).',
          'Registration fee: 1%, capped at ₹30,000.',
          'GST, only on a flat still being built: 5% of the agreement value, about ₹3.75 lakh here. 1% for affordable housing (up to ₹45 lakh and 90 sq m carpet area in Pune). No GST on a ready flat that has its occupancy certificate (OC).',
          'So the same ₹75 lakh flat can cost about ₹84 lakh if it is under construction, and about ₹80.5 lakh if it is ready with an OC, before loan fees, parking, maintenance deposit and society charges.',
        ],
      },
      {
        heading: "'Zero stamp duty' or 'stamp duty paid by us'",
        paragraphs: [
          'The builder pays the stamp duty for you. In the example that is worth about ₹5.25 lakh, which is a real saving, as long as the agreement value has not gone up to cover it.',
          'Stamp duty is charged on the agreement value or the government ready reckoner value, whichever is higher. A builder cannot make it smaller by writing a lower value.',
        ],
        bullets: [
          'Ask for the cost sheet the project gave a month ago, or ask for the price with the offer and without it.',
          'Get the offer written into the booking form or allotment letter, not only in the advert.',
        ],
      },
      {
        heading: "'No EMI till possession' (subvention schemes)",
        paragraphs: [
          'Your home loan is sanctioned and paid to the builder in stages. Under the scheme the builder pays the interest (the pre-EMI) until possession, so you pay nothing for a while.',
          'The catch is the date. The loan is in your name. If possession moves later than the date the scheme covers, or the builder stops paying, the bank will ask you to pay, and a missed payment shows on your credit record.',
        ],
        bullets: [
          'Ask until which date, exactly, the builder pays the interest, and what happens after it.',
          'Read the tripartite agreement (you, the builder and the bank) before you sign it.',
          "Check whether the project's completion date on MahaRERA has already moved since it was registered. Our project pages show the date at registration and the date filed now.",
        ],
      },
      {
        heading: 'Gold coins, free kitchens, free parking',
        bullets: [
          'Put a value on each gift: what would you pay for it yourself? Then ask for that amount off the price instead.',
          'A covered parking space must be written into the agreement, not only promised at the sales desk.',
          'A discount lowers your stamp duty and GST too. A gift does not.',
        ],
      },
      {
        heading: 'Booking on Dhanteras or Diwali',
        paragraphs: [
          'Dhanteras falls on 6 November 2026 and Diwali on 8 November. A good day to book is not a reason to skip the checks: a booking amount is hard to get back once paid.',
        ],
        bullets: [
          'Under the RERA Act, the builder may not take more than 10% of the cost as an advance before a registered agreement for sale.',
          'Ask for the refund terms of the booking amount in writing.',
          'Look the project up on MahaRERA: the registration number, the completion date filed, and the quarterly updates.',
          'If you want to register the agreement on the day itself, book the sub-registrar appointment early.',
        ],
      },
      {
        heading: 'Ready, or still being built?',
        paragraphs: [
          'A ready flat with an OC saves the GST and the wait, and you can see exactly what you are buying. A flat still being built usually gives more choice of floor and layout, but you take on the risk that the completion date moves.',
          'Our weekly "Number of the week" reel is drawn from MahaRERA records, for example how many projects in Kharadi, Wagholi or Lohegaon have a completion date filed for the next 12 months.',
        ],
      },
      {
        heading: 'Ask for these in writing',
        bullets: [
          'The full cost sheet, with the offer and without it',
          'The offer itself, in the booking form or allotment letter',
          'The possession date in the agreement, compared with the date on MahaRERA',
          'For subvention: the date until which the builder pays the interest, and what happens after',
          'The refund terms of the booking amount',
        ],
      },
    ],
    sources: [
      { label: 'IGR Maharashtra (stamp duty and registration)', href: 'https://igrmaharashtra.gov.in/' },
      { label: 'MahaRERA (official portal)', href: 'https://maharera.maharashtra.gov.in/' },
      { label: 'CBIC GST (rates)', href: 'https://cbic-gst.gov.in/' },
    ],
  },
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
