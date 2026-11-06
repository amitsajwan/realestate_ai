import { getAgent, getListings, getSitemapEntries } from './api'
import type { AgentOffer } from './finderItems'
import { isSampleListing } from './format'
import { enquiryName } from './theme'
import type { PublicListing } from './types'

/** Priced home types, then photos: which of several agents' listings a project shows, as on its page (backend listings.projectlive). */
function richness(l: PublicListing): number {
  return (l.configurations ?? []).filter((c) => c.price_inr).length * 100 + (l.media ?? []).length
}

/** The live listings of every agent in the sitemap, by MahaRERA number: on this list an agent-listed project shows their sheet. */
export async function agentOffers(): Promise<Map<string, AgentOffer>> {
  const entries = (await getSitemapEntries()).listings
  const slugs = Array.from(new Set(entries.filter((e) => e.rera_no).map((e) => e.agent_slug)))
  const out = new Map<string, AgentOffer>()
  for (const slug of slugs) {
    const [agent, { items }] = await Promise.all([getAgent(slug).catch(() => null), getListings(slug).catch(() => ({ items: [] as PublicListing[] }))])
    if (!agent) continue
    for (const l of items) {
      const regno = (l.rera_no || '').trim().toUpperCase()
      const have = out.get(regno)
      if (regno && !isSampleListing(l.title) && (!have || richness(l) > richness(have.listing))) out.set(regno, { agentName: enquiryName(agent), listing: l })
    }
  }
  return out
}
