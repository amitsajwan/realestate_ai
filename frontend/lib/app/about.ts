import type { About, AboutNearby, NearbyType } from './types'

export const MAX_TEXT = 300
export const MAX_HIGHLIGHTS = 6
export const MAX_FAQ_UI = 4

export const AMENITY_CHIPS = ['Parking', 'Lift', 'Gym', 'Swimming pool', 'Security', 'Power backup', 'Garden', 'Clubhouse', 'Play area', '24x7 water', 'Intercom', 'Terrace']

export const NEARBY_CHIPS: Array<{ type: NearbyType; label: string }> = [
  { type: 'school', label: 'School nearby' },
  { type: 'hospital', label: 'Hospital nearby' },
  { type: 'market', label: 'Market nearby' },
  { type: 'park', label: 'Park nearby' },
  { type: 'transit', label: 'Bus stop nearby' },
  { type: 'office', label: 'Offices nearby' },
]

export const FAQ_PRESETS = ['Is parking included?', 'How much is the maintenance?', 'Is water supply 24x7?', 'Is there a lift and power backup?']

const PHONE = /(?<!\d)(?:\+?\d[\s\-.()]*){10,}(?!\d)/
const URL = /https?:\/\/|www\.|(?<![\w.])[a-z0-9-]+\.(?:com|in|co|org|net|io|app|me|ly|info)(?:\/|\b)/i

/** Same rules the server enforces (422 otherwise): returns a plain message, or null when the text is fine. */
export function textProblem(v: string): string | null {
  if (v.length > MAX_TEXT) return `Please keep it under ${MAX_TEXT} characters.`
  if (PHONE.test(v)) return 'Please do not type phone numbers here. Buyers reach you through your link.'
  if (URL.test(v)) return 'Please do not type links here.'
  return null
}

export function aboutProblem(a: About): string | null {
  const texts: string[] = [
    a.project_name, a.water, a.power_backup, a.maintenance, a.society, a.parking,
    ...(a.highlights ?? []), ...(a.amenities ?? []), ...(a.connectivity ?? []),
    ...(a.nearby ?? []).map((n) => n.name), ...(a.faq ?? []).flatMap((f) => [f.q, f.a]),
  ].filter((x): x is string => typeof x === 'string' && x !== '')
  for (const t of texts) {
    const p = textProblem(t)
    if (p) return p
  }
  return null
}

/** Trim and drop empties so the stored object only holds what the agent gave. Returns undefined when nothing is left. */
export function compactAbout(a: About | null | undefined): About | undefined {
  if (!a) return undefined
  const out: About = {}
  const str = (v?: string | null) => (v ?? '').trim()
  for (const k of ['project_name', 'builder_known_as', 'water', 'power_backup', 'maintenance', 'society', 'parking', 'possession_note', 'rera_note'] as const) {
    if (str(a[k])) out[k] = str(a[k])
  }
  for (const k of ['highlights', 'amenities', 'connectivity'] as const) {
    const list = (a[k] ?? []).map((x) => x.trim()).filter(Boolean)
    if (list.length) out[k] = Array.from(new Set(list))
  }
  const nearby = (a.nearby ?? []).filter((n) => n.name.trim()).map((n): AboutNearby => ({ type: n.type, name: n.name.trim(), ...(typeof n.minutes === 'number' ? { minutes: n.minutes } : {}) }))
  if (nearby.length) out.nearby = nearby
  const faq = (a.faq ?? []).filter((f) => f.q.trim() && f.a.trim()).map((f) => ({ q: f.q.trim(), a: f.a.trim() })).slice(0, MAX_FAQ_UI)
  if (faq.length) out.faq = faq
  return Object.keys(out).length ? out : undefined
}

/** One short line per filled part, for the review summary. */
export function aboutSummaryLines(a: About | null | undefined): string[] {
  const c = compactAbout(a)
  if (!c) return []
  const lines: string[] = []
  if (c.project_name) lines.push(c.project_name)
  if (c.highlights?.length) lines.push(c.highlights.join(', '))
  if (c.amenities?.length) lines.push(c.amenities.join(', '))
  if (c.nearby?.length) lines.push(c.nearby.map((n) => n.name).join(', '))
  const facts = [c.parking, c.water, c.power_backup, c.maintenance, c.society].filter(Boolean)
  if (facts.length) lines.push(facts.join(' · '))
  if (c.connectivity?.length) lines.push(`${c.connectivity.length} connectivity note${c.connectivity.length > 1 ? 's' : ''}`)
  if (c.faq?.length) lines.push(`${c.faq.length} buyer question${c.faq.length > 1 ? 's' : ''} answered`)
  return lines
}
