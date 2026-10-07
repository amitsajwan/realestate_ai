/**
 * The website chat's reply (POST /api/v1/chat/message) and small helpers for showing it. All decisions are on the server; this only
 * reads the reply defensively (an older server sends no cards and no WhatsApp link, and that is fine).
 */
export interface ChatCard {
  id: string
  title: string
  locality?: string | null
  bhk?: number | null
  carpet_sqft?: number | null
  /** null for samples: a sample is an illustration and has no real price */
  price_text?: string | null
  sample: boolean
  url: string
  image_url?: string | null
}

export interface ChatReply {
  reply: string
  quick_replies: string[]
  lead_created: boolean
  cards: ChatCard[]
  /** with cards: the next question, shown after them */
  follow_up: string | null
  /** set only when the platform WhatsApp number is configured */
  whatsapp_url: string | null
}

export const WHATSAPP_QUICK = 'Continue on WhatsApp'

const SAFE_URL = /^(\/(?!\/)|https:\/\/)/

function str(v: unknown): string | null {
  return typeof v === 'string' && v.trim() ? v : null
}

function num(v: unknown): number | null {
  return typeof v === 'number' && isFinite(v) && v > 0 ? v : null
}

/** Only same-site paths and https links are used as hrefs or image sources. */
export function safeUrl(v: unknown): string | null {
  const s = str(v)
  return s && SAFE_URL.test(s) ? s : null
}

export function parseChatReply(data: unknown): ChatReply {
  const d = (data && typeof data === 'object' ? data : {}) as Record<string, unknown>
  const cards: ChatCard[] = Array.isArray(d.cards)
    ? (d.cards as Record<string, unknown>[])
        .map((c) => ({
          id: String(c?.id ?? ''),
          title: str(c?.title) ?? 'Home',
          locality: str(c?.locality),
          bhk: num(c?.bhk),
          carpet_sqft: num(c?.carpet_sqft),
          price_text: c?.sample ? null : str(c?.price_text),
          sample: Boolean(c?.sample),
          url: safeUrl(c?.url) ?? '',
          image_url: safeUrl(c?.image_url),
        }))
        .filter((c) => c.id && c.url)
        .slice(0, 3)
    : []
  const wa = safeUrl(d.whatsapp_url)
  const whatsapp = wa && wa.startsWith('https://wa.me/') ? wa : null
  const quick = Array.isArray(d.quick_replies) ? (d.quick_replies as unknown[]).filter((q): q is string => typeof q === 'string') : []
  return {
    reply: str(d.reply) ?? '',
    // 'Continue on WhatsApp' only with a real link to open
    quick_replies: quick.filter((q) => q !== WHATSAPP_QUICK || !!whatsapp),
    lead_created: Boolean(d.lead_created),
    cards,
    follow_up: str(d.follow_up),
    whatsapp_url: whatsapp,
  }
}

/** "Kharadi · 2 BHK · 780 sq ft" */
export function cardFacts(c: ChatCard): string {
  const bhk = c.bhk ? `${Number.isInteger(c.bhk) ? c.bhk : c.bhk.toFixed(1)} BHK` : ''
  const area = c.carpet_sqft ? `${Math.round(c.carpet_sqft).toLocaleString('en-IN')} sq ft` : ''
  return [c.locality || '', bhk, area].filter(Boolean).join(' · ')
}
