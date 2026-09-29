/** Fixture-mode logic for social publishing (docs/contracts/social.md): always a dry run, both channels configured. */
import type { MarketingPack, Publication, SocialChannel, SocialPublishRequest, SocialStatus } from './types'

export const FIXTURE_SOCIAL_STATUS: SocialStatus = {
  dry_run: true,
  channels: { facebook_page: true, instagram: true },
  brand: 'PUNE Property',
  media_url_ok: false,
}

const CONSENT_TEXT = 'I agree to post this listing, with my name and phone number, on the PUNE Property Page.'

function payloadFor(pack: MarketingPack, channel: SocialChannel): Publication['payload'] {
  if (channel === 'facebook_page') {
    const cover = pack.instagram.images.find((i) => i.kind === 'cover') ?? pack.instagram.images[0]
    return { text: `${pack.facebook.post}\n${pack.share_url}`, image_urls: cover ? [cover.url] : [] }
  }
  const tags = pack.instagram.hashtags.map((h) => `#${h.replace(/^#+/, '')}`).join(' ')
  return {
    text: tags ? `${pack.instagram.caption}\n\n${tags}` : pack.instagram.caption,
    image_urls: pack.instagram.images.map((i) => i.url),
  }
}

/** New dry-run publications for the requested channels. The caller has already checked approve/consent/pack/listing. */
export function buildPublications(
  pack: MarketingPack,
  agentId: string,
  req: SocialPublishRequest,
  nextId: () => string,
  now: string,
): Publication[] {
  return req.channels.map((channel) => ({
    id: nextId(),
    listing_id: pack.listing_id,
    agent_id: agentId,
    channel,
    pack_version: pack.version,
    status: 'dry_run' as const,
    external_id: null,
    permalink: null,
    error: null,
    consent: { given_at: now, text: CONSENT_TEXT },
    approved_at: now,
    created_at: now,
    updated_at: now,
    attempts: 1,
    payload: payloadFor(pack, channel),
  }))
}
