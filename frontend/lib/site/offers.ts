import { getAgent, getListings, getSitemapEntries } from './api'
import type { AgentOffer } from './finderItems'
import { isSampleListing } from './format'
import { enquiryName } from './theme'
import type { PublicListing } from './types'

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
      if (regno && !out.has(regno) && !isSampleListing(l.title)) out.set(regno, { agentName: enquiryName(agent), listing: l })
    }
  }
  return out
}
