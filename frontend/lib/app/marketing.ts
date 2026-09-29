/** Pure helpers for the marketing pack screen (docs/contracts/marketing.md). Nothing here sends anything. */
import { waDigits } from './format'
import { whatsappChatUrl, whatsappShareUrl } from './share'
import type { ImageAsset, MarketingPack, MatchingBuyer, RecommendedAction, ReelBeat } from './types'

/** ["#Baner", "Pune"] -> "#Baner #Pune" (adds a missing #, drops empties and duplicates). */
export function hashtagsLine(tags: string[]): string {
  const seen = new Set<string>()
  const out: string[] = []
  for (const raw of tags) {
    const tag = raw.trim().replace(/^#+/, '').replace(/\s+/g, '')
    if (!tag || seen.has(tag.toLowerCase())) continue
    seen.add(tag.toLowerCase())
    out.push(`#${tag}`)
  }
  return out.join(' ')
}

/** What the agent pastes into Instagram: caption, blank line, hashtags. */
export function instagramCopyText(ig: MarketingPack['instagram']): string {
  const tags = hashtagsLine(ig.hashtags)
  return tags ? `${ig.caption}\n\n${tags}` : ig.caption
}

/** Hook first, one numbered line per beat with the visual note, call to action last. */
export function reelScriptText(reel: MarketingPack['reel']): string {
  const beats = reel.beats.map((b: ReelBeat, i) => `${i + 1}. (${b.seconds}) ${b.text}\n   Show: ${b.visual}`)
  return [`Hook: ${reel.hook}`, ...beats, `Call to action: ${reel.cta}`].join('\n')
}

/** wa.me link that lets the agent pick a contact and pre-fills the text. */
export function whatsappPackUrl(text: string): string {
  return whatsappShareUrl(text)
}

/** wa.me link to one buyer with a (possibly edited) message. Empty message opens the chat without text. */
export function buyerWhatsappUrl(phone: string, message: string): string {
  return whatsappChatUrl(waDigits(phone), message.trim() ? message : undefined)
}

/** Use the server-built link while the draft is unedited; rebuild it once the agent changed the words. */
export function buyerDraftUrl(buyer: MatchingBuyer, message: string): string {
  if (message === buyer.draft.message && buyer.draft.whatsapp_url) return buyer.draft.whatsapp_url
  return buyerWhatsappUrl(buyer.phone, message)
}

export function imageFilename(image: ImageAsset, listingId: string): string {
  const ext = /^data:image\/svg/.test(image.url) ? 'svg' : /\.png(\?|$)/i.test(image.url) ? 'png' : 'jpg'
  return `${listingId}-${image.kind}.${ext}`
}

/** Where an AI recommendation card leads. Call opens the buyer (their number and Call button are on that screen). */
export function actionHref(a: RecommendedAction): string {
  switch (a.type) {
    case 'call':
    case 'follow_up':
      return a.lead_id ? `/studio/leads/${a.lead_id}` : '/studio/leads'
    case 'send_property':
    case 'create_marketing':
      return a.listing_id ? `/studio/listings/${a.listing_id}/marketing` : '/studio/listings'
  }
}

export type ShareOutcome = 'shared' | 'downloaded' | 'opened' | 'cancelled'

/** Download an image URL; falls back to opening it in a new tab (cross-origin URLs can block fetch). */
export async function downloadImage(image: ImageAsset, filename: string): Promise<'downloaded' | 'opened'> {
  try {
    const blob = await (await fetch(image.url)).blob()
    const href = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = href
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(href), 1000)
    return 'downloaded'
  } catch {
    window.open(image.url, '_blank', 'noopener,noreferrer')
    return 'opened'
  }
}

/** Share the image file with the caption where the phone supports it, otherwise download / open it. */
export async function shareImage(image: ImageAsset, filename: string, text: string): Promise<ShareOutcome> {
  try {
    if (typeof navigator !== 'undefined' && typeof navigator.share === 'function' && typeof navigator.canShare === 'function') {
      const blob = await (await fetch(image.url)).blob()
      const file = new File([blob], filename, { type: blob.type || 'image/jpeg' })
      if (navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], text })
        return 'shared'
      }
    }
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') return 'cancelled'
    // fall through to download
  }
  return downloadImage(image, filename)
}
