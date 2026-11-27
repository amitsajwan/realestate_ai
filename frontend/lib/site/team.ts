import { TEAM as TEAM_NAME } from '@/lib/brand'
import { getMarketingConfig } from '@/lib/marketing/config'
import { waNumber } from './phone'

/**
 * Who answers for Avasetu, and how to reach them: the footer of every public page, About, Contact and the Organization in the
 * structured data all read it from here, so a change is made once.
 *
 * Avasetu is run by its own team (owner 2026-11-27: "we don't need a partner yet"). No agent is the team behind the site or its
 * partner: agents list homes here, each listing says whose it is, and that is all the site says about them. From 2026-11-13 to
 * 2026-11-27 this named House Deal, an agent, as the team, with its office, phone and MahaRERA agent number.
 *
 * Why it is on the site at all: buying a home is a money decision, and Google's raters look for who is responsible for such a site
 * and a way to reach them (Search Quality Rater Guidelines 2.5.2, 2.5.3). The ways to reach the team are the site's own settings,
 * nothing typed here: the WhatsApp number the assistant answers (NEXT_PUBLIC_WHATSAPP_NUMBER, as the project pages' WhatsApp
 * buttons use it) and the contact email (NEXT_PUBLIC_CONTACT_EMAIL, as on the legal pages). An unset one is not shown.
 */
export interface SiteTeam {
  name: string
  /** what the team does, said the same way wherever it is said */
  what: string
  whatsappDigits: string | null
  /** '+91 98342 56406' */
  whatsappDisplay: string | null
  whatsappUrl: string | null
  email: string | null
}

function display(digits: string): string {
  return /^91[6-9]\d{9}$/.test(digits) ? '+91 ' + digits.slice(2, 7) + ' ' + digits.slice(7) : '+' + digits
}

export function siteTeam(env: { whatsapp?: string; email?: string | null } = {}): SiteTeam {
  const wa = waNumber(env.whatsapp ?? process.env.NEXT_PUBLIC_WHATSAPP_NUMBER)
  return {
    name: TEAM_NAME,
    what: 'checks Pune projects against MahaRERA, answers every enquiry sent from this website and fixes a page when someone tells us it is wrong',
    whatsappDigits: wa,
    whatsappDisplay: wa ? display(wa) : null,
    whatsappUrl: wa ? 'https://wa.me/' + wa : null,
    email: env.email !== undefined ? env.email : getMarketingConfig().email,
  }
}

/** The Avasetu Organization's node id, so the WebSite's `publisher` (home page) points at it instead of a second copy. */
export const organizationId = (siteUrl: string): string => siteUrl + '/#organization'

/** What the Avasetu Organization adds about who answers: the team's WhatsApp and email. No parent organization and no office:
 *  Avasetu belongs to no agent. Merged into the Organization on the home, About and Contact pages. */
export function teamForOrganization(siteUrl: string, team: SiteTeam = siteTeam()): Record<string, unknown> {
  const point = {
    '@type': 'ContactPoint', contactType: 'customer service', areaServed: 'IN', availableLanguage: ['English', 'Hindi', 'Marathi'],
    ...(team.whatsappDigits ? { telephone: '+' + team.whatsappDigits } : {}), ...(team.email ? { email: team.email } : {}),
  }
  return { '@id': organizationId(siteUrl), ...(team.whatsappDigits || team.email ? { contactPoint: [point] } : {}) }
}
