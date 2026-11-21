/**
 * Public social profiles and the contact wording. There is deliberately no phone number, email or personal name here:
 * contact is the website, the Facebook Page and Instagram. Override with NEXT_PUBLIC_FACEBOOK_URL / NEXT_PUBLIC_INSTAGRAM_URL
 * (the owner renames the Page and the Instagram handle to Avasetu by hand; the defaults are the current profile URLs).
 */
import { BRAND_NAME } from '@/lib/brand'
export const DEFAULT_FACEBOOK_URL = 'https://www.facebook.com/profile.php?id=61594653947865'
export const DEFAULT_INSTAGRAM_URL = 'https://www.instagram.com/avasetu_/'

const https = (v: string | undefined, fallback: string) => (v && /^https:\/\/[^\s]+$/.test(v.trim()) ? v.trim() : fallback)

export function socialLinks(): { facebook: string; instagram: string } {
  return {
    facebook: https(process.env.NEXT_PUBLIC_FACEBOOK_URL, DEFAULT_FACEBOOK_URL),
    instagram: https(process.env.NEXT_PUBLIC_INSTAGRAM_URL, DEFAULT_INSTAGRAM_URL),
  }
}

/** The brand's other public profiles, added here as each one goes live and shows "Avasetu" with a link to avasetu.in
 *  (owner 2026-11-20: LinkedIn company page, the YouTube channel once it has public videos, Crunchbase, directories). They join
 *  Facebook and Instagram in the Organization's `sameAs`, which is how Google learns that "avasetu" is a name and not a
 *  misspelling of "Seva Setu". Only a profile that exists: an empty or bare site address (https://linkedin.com) tells Google nothing. */
export const MORE_PROFILES: readonly string[] = [
  // the company page, live 2026-11-21: Avasetu, Pune, linking https://avasetu.in
  'https://www.linkedin.com/company/avasetu/',
]

/** Every public profile of the brand, for the Organization's `sameAs`: Facebook, Instagram, then MORE_PROFILES. A profile must be
 *  an https address with a path (a page of its own, not a site's front page); duplicates are dropped. */
export function brandProfiles(more: readonly string[] = MORE_PROFILES): string[] {
  const own = (v: string) => /^https:\/\/[^\s/]+\/[^\s]+$/.test(v.trim())
  const all = [...Object.values(socialLinks()), ...more.map((v) => v.trim()).filter(own)]
  return all.filter((v, i) => all.indexOf(v) === i)
}

export const CONTACT = {
  heading: `Contact ${BRAND_NAME}`,
  // buyers first (tap I am interested, or the chat), then the social profiles; agents last, in one short line
  before: 'Ask about any home on this website: tap I am interested, or use the chat. You can also message us on ',
  facebook: 'Facebook',
  and: ' or ',
  instagram: 'Instagram',
  after: '. ',
  agents: 'Agents can ',
  invite: 'request an invite',
  end: '.',
  follow: 'Follow us',
}
