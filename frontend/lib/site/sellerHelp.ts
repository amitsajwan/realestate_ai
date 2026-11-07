import { contactName, PROJECT_CTA } from './strings'

/** What a project page may promise the buyer, from what stands behind it. The page's caution stays honest either way, but who does
 *  the checking changes: "confirm with the builder" sent a lead away from us, so where someone can act the page says they will,
 *  and where nobody can it promises nothing (docs/plan/project-page-v2.md, "Seller voice").
 *  sheet: an agent's price sheet; covered: an agent's page, or House Deal's areas; ask: elsewhere; closed: no enquiries. */
export type Backing = 'sheet' | 'covered' | 'ask' | 'closed'

/** House Deal's six areas (owner 2026-10-30). The lead rules that pass these on live in the database and can be empty; this list is
 *  what the team stands behind on the page. */
const COVERED = new Set(['upper-kharadi', 'kharadi', 'wagholi', 'mundhwa', 'hadapsar', 'keshav-nagar'])

interface Where { area?: { slug: string } | null; pune_place?: { key: string } | null }

export function backing(p: Where, page: { closed: boolean; offer: boolean; seller: boolean }): Backing {
  if (page.closed) return 'closed'
  if (page.offer) return 'sheet'
  if (page.seller) return 'covered'
  const place = p.pune_place?.key.replace(/_/g, '-')
  return (p.area && COVERED.has(p.area.slug)) || (place && COVERED.has(place)) ? 'covered' : 'ask'
}

const opening = (who: string) => who.charAt(0).toUpperCase() + who.slice(1)

export interface PriceHelpText { title: string; body: string; action: string }

/** The panel under a project's prices: what the buyer gets by asking. Nothing on a closed page. */
export function priceHelp(b: Backing, agentName: string): PriceHelpText | null {
  const who = contactName(agentName)
  if (b === 'sheet') return { title: "Want this at today's price?", body: `Prices change. ${opening(who)} confirms today's price, what is still available and the full cost.`, action: PROJECT_CTA.offer }
  if (b === 'covered') return { title: 'Get the exact price for your home', body: `${opening(who)} gets you the current price sheet for the size you want, with parking and all other charges.`, action: PROJECT_CTA.offer }
  if (b === 'ask') return { title: 'Ask about this project', body: `This project is outside our main East Pune areas. Send your question and ${who} tells you what we can find out.`, action: PROJECT_CTA.question }
  return null
}

/** Under the home sizes: who confirms a carpet area, only where someone stands behind the page. */
export function sizeHelp(b: Backing, agentName: string): string | null {
  return b === 'sheet' || b === 'covered' ? `Tell us the home you like and ${contactName(agentName)} confirms its size.` : null
}
