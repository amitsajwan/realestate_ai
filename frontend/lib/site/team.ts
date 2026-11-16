/**
 * The team behind Avasetu: House Deal, a MahaRERA-registered agent's office in Upper Kharadi (owner 2026-11-13: "use House
 * Deal's contact as the main contact, let it be the main team behind it").
 *
 * Why it is on the site at all: buying a home is a money decision, and Google's raters look for who is responsible for such a
 * site, with an address and a way to reach them (Search Quality Rater Guidelines 2.5.2, 2.5.3). Until 2026-11-13 the site named
 * no one and /contact answered 404. Every value here is what House Deal publishes about itself on house-deal.com and on its own
 * page here (/agent/house-deal); change them in this one place.
 */
export const TEAM = {
  name: 'House Deal',
  /** what House Deal is, in the words of its own page */
  what: 'a property advisory office for new projects across East Pune',
  street: '1107, RTC Silver, Upper Kharadi, Wagholi',
  locality: 'Pune',
  postalCode: '412207',
  region: 'Maharashtra',
  /** shown as written; dialled from `tel` */
  phone: '+91 74472 12121',
  tel: '+917447212121',
  email: 'housedealofficial@gmail.com',
  /** MahaRERA's registration number for House Deal as a real estate agent */
  rera: 'A031262502865',
  website: 'https://house-deal.com',
  page: '/agent/house-deal',
} as const

/** The address on one line, as a letter would carry it. */
export const teamAddress = (): string => `${TEAM.street}, ${TEAM.locality} ${TEAM.postalCode}`

/** House Deal as schema.org data: the real estate agent, its MahaRERA number, office and phone. */
export function teamJsonLd(siteUrl: string): Record<string, unknown> {
  return {
    '@type': 'RealEstateAgent',
    name: TEAM.name,
    url: TEAM.website,
    sameAs: [siteUrl + TEAM.page],
    identifier: { '@type': 'PropertyValue', propertyID: 'MahaRERA', value: TEAM.rera },
    address: teamPostalAddress(),
    telephone: TEAM.tel,
    email: TEAM.email,
    areaServed: { '@type': 'City', name: 'Pune' },
  }
}

export function teamPostalAddress(): Record<string, unknown> {
  return {
    '@type': 'PostalAddress', streetAddress: TEAM.street, addressLocality: TEAM.locality, postalCode: TEAM.postalCode,
    addressRegion: TEAM.region, addressCountry: 'IN',
  }
}

/** What the Avasetu Organization adds about who runs it: its office (House Deal's), a phone and email that answer, and House
 *  Deal as the team (`member`). Merged into the Organization on the home, About and Contact pages. */
export function teamForOrganization(siteUrl: string): Record<string, unknown> {
  return {
    address: teamPostalAddress(),
    contactPoint: [{ '@type': 'ContactPoint', contactType: 'customer service', telephone: TEAM.tel, email: TEAM.email,
      areaServed: 'IN', availableLanguage: ['English', 'Hindi'] }],
    member: [teamJsonLd(siteUrl)],
  }
}
