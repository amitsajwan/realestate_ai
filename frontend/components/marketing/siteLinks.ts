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

export function siteLinks() {
  const { instagram, facebook } = socialLinks()
  const forAgents: SiteLink = { href: FOR_AGENTS_PATH, label: 'For agents' }
  const demo: SiteLink = { href: demoAgentPath(), label: 'See a demo page' }
  const news: SiteLink = { href: '/news', label: 'News' }
  const posts: SiteLink = { href: '/posts', label: 'Posts' }
  const areas: SiteLink = { href: '/localities', label: 'Area guides' }
  const insights: SiteLink = { href: '/insights', label: 'Insights' }
  const invite: SiteLink = { href: INVITE_PATH, label: 'Join the free pilot' }
  const signIn: SiteLink = { href: SIGN_IN_PATH, label: 'Sign in' }
  const ig: SiteLink = { href: instagram, label: 'Instagram', external: true }
  const fb: SiteLink = { href: facebook, label: 'Facebook', external: true }
  return {
    forAgents, demo, news, posts, areas, insights, invite, signIn, instagram: ig, facebook: fb,
    /** Header, wide screens (the invite button sits next to these). */
    headerWide: [forAgents, demo, news, areas],
    /** Header menu on phones: everything. */
    menu: [forAgents, demo, news, posts, areas, insights, signIn, ig, fb],
    footerAgents: [forAgents, demo, invite, signIn],
    footerExplore: [news, posts, areas, insights],
    footerFollow: [ig, fb],
  }
}
