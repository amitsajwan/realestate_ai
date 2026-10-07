/** Pure helpers for the "Post to Avasetu" section (docs/contracts/social.md). Nothing here sends anything. */
import { ApiError } from './api'
import { t } from './strings'
import type { Publication, PublicationStatus, SocialChannel } from './types'
import { BRAND_NAME } from '@/lib/brand'

export const SOCIAL_CHANNELS: SocialChannel[] = ['facebook_page', 'instagram']

export const SOCIAL_CONSENT_TEXT = `I agree to post this listing, on the ${BRAND_NAME} Page.`

export function channelLabel(c: SocialChannel): string {
  return c === 'facebook_page' ? t('socialFacebookPage') : t('socialInstagram')
}

export function statusLabel(s: PublicationStatus): string {
  switch (s) {
    case 'published':
      return t('socialPosted')
    case 'dry_run':
      return t('socialTestPost')
    case 'failed':
      return t('socialFailed')
    case 'queued':
      return t('socialQueued')
  }
}

export function statusTone(s: PublicationStatus): string {
  return { published: 'green', dry_run: 'blue', failed: 'red', queued: 'amber' }[s]
}

/** A post that already went out (for real or as a test), so the same pack version is not posted twice by accident. */
export function isDone(p: Publication): boolean {
  return p.status === 'published' || p.status === 'dry_run'
}

/** Channels already posted for this exact pack version. */
export function doneChannels(pubs: Publication[], packVersion: number): Set<SocialChannel> {
  return new Set(pubs.filter((p) => isDone(p) && p.pack_version === packVersion).map((p) => p.channel))
}

/** Plain-language reason for a failed post. The raw text stays available as "Details". */
export function friendlyPublishError(error: string | null): string {
  const e = (error ?? '').toLowerCase()
  if (/not configured/.test(e)) return t('socialErrNotConfigured')
  if (/token|oauth|permission|expired|unauthori[sz]ed|access/.test(e)) return t('socialErrAccount')
  if (/image|photo|media|container/.test(e)) return t('socialErrImage')
  return t('socialErrGeneric')
}

/** Friendly message for a failed publish request. 422 never happens from the UI. */
export function publishRequestError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 409) return /already|posted/i.test(e.detail) ? t('socialAlreadyPosted') : t('socialNotReady')
    if (e.isNetwork) return e.detail
    return t('socialErrGeneric')
  }
  return t('socialErrGeneric')
}
