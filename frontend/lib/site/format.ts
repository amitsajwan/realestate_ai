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

/** An illustrative listing (title starts with "Sample"): labelled on the site and never presented as available. */
export function isSampleListing(title?: string | null): boolean {
  return (title || '').trim().toLowerCase().startsWith('sample')
}
