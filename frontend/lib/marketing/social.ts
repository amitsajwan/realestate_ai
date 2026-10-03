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

export const CONTACT = {
  heading: `Contact ${BRAND_NAME}`,
  before: `Contact ${BRAND_NAME} via this website (`,
  invite: 'request an invite',
  middle: ', or tap I am interested on any home), ',
  facebook: 'Facebook',
  and: ' and ',
  instagram: 'Instagram',
  after: '.',
  follow: 'Follow us',
}
