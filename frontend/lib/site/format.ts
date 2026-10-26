import type { Transaction } from './types'

const trim = (n: number, digits: number): string => {
  const s = n.toFixed(digits)
  return s.indexOf('.') >= 0 ? s.replace(/0+$/, '').replace(/\.$/, '') : s
}

/** Indian digit grouping: 4500000 -> "45,00,000". */
export function groupIndian(n: number): string {
  const s = String(Math.round(Math.abs(n)))
  if (s.length <= 3) return s
  const last3 = s.slice(-3)
  const rest = s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',')
  return rest + ',' + last3
}

/**
 * Format rupees: 8500000 -> "85 L", 12500000 -> "1.25 Cr".
 * Rent (per month) -> "₹45,000/mo". Use formatPrice for display with a rupee sign.
 */
export function formatInr(amount: number, transaction: Transaction = 'sale'): string {
  if (!isFinite(amount) || amount < 0) return ''
  if (transaction === 'rent') return '₹' + groupIndian(amount) + '/mo'
  if (amount >= 10000000) return trim(amount / 10000000, 2) + ' Cr'
  if (amount >= 100000) return trim(amount / 100000, 2) + ' L'
  return '₹' + groupIndian(amount)
}

/** Display price with a rupee sign: "₹85 L", "₹1.25 Cr", "₹45,000/mo". */
export function formatPrice(amount: number, transaction: Transaction = 'sale'): string {
  const s = formatInr(amount, transaction)
  return s === '' || s.charAt(0) === '₹' ? s : '₹' + s
}

export function formatArea(sqft?: number | null): string {
  if (!sqft || sqft <= 0) return ''
  return groupIndian(sqft) + ' sq.ft'
}

export function titleCase(s: string): string {
  return s
    .replace(/[_-]+/g, ' ')
    .split(' ')
    .map((w) => (w ? w.charAt(0).toUpperCase() + w.slice(1) : w))
    .join(' ')
}

// short forms that stay in capitals when a shouted name is put in normal case
const KEEP_CAPS = new Set(['LLP', 'LLC', 'HUF', 'II', 'III', 'IV', 'VJ', 'IT', 'SRA', 'MHADA', 'PMC', 'PCMC', 'PMRDA'])

/** A name MahaRERA has in capitals ("SOHAM ASSOCIATES", "ZEN ELITE") as people write it ("Soham Associates"); a name that
 *  already has small letters is left as its builder wrote it ("VJ Central Avenue", "Neco Park Central"). */
export function readableName(s: string | null | undefined): string {
  const t = (s || '').trim()
  if (!/[A-Z]/.test(t) || /[a-z]/.test(t)) return t
  return t.replace(/[A-Z0-9][A-Z0-9'&.]*/g, (w) => (KEEP_CAPS.has(w) || /\d/.test(w) ? w : w.charAt(0) + w.slice(1).toLowerCase()))
}

export function bhkLabel(bhk?: number | null, propertyType?: string): string {
  if (bhk && bhk > 0) return trim(bhk, 1) + ' BHK'
  if (propertyType) return titleCase(propertyType)
  return ''
}

const FURNISHING: Record<string, string> = {
  unfurnished: 'Unfurnished',
  semi: 'Semi-furnished',
  furnished: 'Fully furnished',
}
export const furnishingLabel = (f?: string | null): string => (f ? FURNISHING[f] || titleCase(f) : '')

export function possessionLabel(p?: string | null): string {
  if (!p) return ''
  if (p === 'ready') return 'Ready to move'
  if (p === 'under_construction') return 'Under construction'
  return p
}

export function floorLabel(floor?: number | null, total?: number | null): string {
  if (floor === null || floor === undefined) return ''
  const f = floor === 0 ? 'Ground' : String(floor)
  return total ? f + ' of ' + total : f
}

export function truncate(s: string, max: number): string {
  const t = (s || '').replace(/\s+/g, ' ').trim()
  return t.length <= max ? t : t.slice(0, max - 1).trimEnd() + '…'
}

/** Google shows about 160 characters of a description and about 70 of a title; anything after that is cut off in the result. */
export const DESCRIPTION_MAX = 160
export const TITLE_MAX = 70

/** Cut at a sentence end if one leaves most of the text, else at a word, never mid-word. */
export function clipWords(s: string, max: number = DESCRIPTION_MAX): string {
  const t = (s || '').replace(/\s+/g, ' ').trim()
  if (t.length <= max) return t
  const sentence = t.slice(0, max).match(/^.*[.!?](?=\s|$)/)
  if (sentence && sentence[0].length >= max / 2) return sentence[0]
  const cut = t.slice(0, max - 1)
  const space = cut.lastIndexOf(' ')
  return (space > 0 ? cut.slice(0, space) : cut).replace(/[\s,;:.(&-]+$/, '') + '…'
}

/** A search description that fits: `write` builds the text, asking `has(n)` whether clause n is still in. Clauses go in order
 *  n = 1, 2, 3... until the text fits, so the page puts its least useful words at 1 and its facts (count, price, possession,
 *  MahaRERA) outside any `has`; whole clauses go, never half a word. Clipped at a word only if even the bare facts are too long. */
export function fitDescription(write: (has: (n: number) => boolean) => string, max: number = DESCRIPTION_MAX): string {
  let text = ''
  for (let level = 0; level <= 12; level++) {
    text = write((n) => n > level).replace(/\s+/g, ' ').trim()
    if (text.length <= max) return text
  }
  return clipWords(text, max)
}

/** The first title that fits Google's ~70 characters, else the last (shortest) one. */
export const fitTitle = (options: string[], max: number = TITLE_MAX): string => options.find((t) => t.length <= max) ?? options[options.length - 1]

/** An illustrative listing (title starts with "Sample"): labelled on the site and never presented as available. */
export function isSampleListing(title?: string | null): boolean {
  return (title || '').trim().toLowerCase().startsWith('sample')
}
