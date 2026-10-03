/**
 * The public site's link map: one list the landing header, footer and the /for-agents page share, so every page links to
 * the same places. Instagram and Facebook come from lib/marketing/social (env overridable); the demo page slug from
 * NEXT_PUBLIC_DEMO_AGENT_SLUG (default 'demo').
 */
import { demoAgentPath } from '@/lib/brand'
import { socialLinks } from '@/lib/marketing/social'

export interface SiteLink {
  href: string
  label: string
  external?: boolean
}

export const FOR_AGENTS_PATH = '/for-agents'
export const INVITE_PATH = '/request-invite'
/** Studio is the agent's app; it sends a signed-out visitor to the sign-in screen (/join). */
export const SIGN_IN_PATH = '/studio'
/** A buyer's 'tell us what you need': the house agent site's existing enquiry form (the same place the area guides send buyers). */
export const buyerEnquirePath = (): string => `/agent/${process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'}#enquire`

/** Who a page is for: buyer pages (home, area guides, insights, news, posts) get the buyer button in the header, agent pages the invite. */
export type Audience = 'buyer' | 'agent'

export function siteLinks() {
  const { instagram, facebook } = socialLinks()
  const forAgents: SiteLink = { href: FOR_AGENTS_PATH, label: 'For agents' }
  const demo: SiteLink = { href: demoAgentPath(), label: 'See a demo page' }
  const news: SiteLink = { href: '/news', label: 'News' }
  const posts: SiteLink = { href: '/posts', label: 'Posts' }
  const areas: SiteLink = { href: '/localities', label: 'Area guides' }
  const projects: SiteLink = { href: '/projects', label: 'Projects' }
  const insights: SiteLink = { href: '/insights', label: 'Insights' }
  const invite: SiteLink = { href: INVITE_PATH, label: 'Join the free pilot' }
  const signIn: SiteLink = { href: SIGN_IN_PATH, label: 'Sign in' }
  const need: SiteLink = { href: buyerEnquirePath(), label: 'Tell us what you need' }
  const ig: SiteLink = { href: instagram, label: 'Instagram', external: true }
  const fb: SiteLink = { href: facebook, label: 'Facebook', external: true }
  return {
    forAgents, demo, news, posts, areas, projects, insights, invite, signIn, need, instagram: ig, facebook: fb,
    /** Header, wide screens, by audience (the buyer or invite button sits next to these; 'For agents' is always there). */
    headerWide: { buyer: [projects, areas, news, forAgents], agent: [forAgents, demo, news, areas] } as Record<Audience, SiteLink[]>,
    /** Header menu on phones: everything. */
    menu: [projects, areas, news, insights, posts, forAgents, demo, signIn, ig, fb],
    footerAgents: [forAgents, demo, invite, signIn],
    footerExplore: [projects, areas, news, posts, insights],
    footerFollow: [ig, fb],
  }
}
