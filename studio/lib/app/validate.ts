import { formatInr, groupIndian } from './format'
import type { ListingInput } from './types'

/** Fields the contract requires to publish (docs/contracts/listing.md). Photos are optional. */
export const PUBLISH_REQUIRED = ['title', 'transaction', 'property_type', 'price_inr', 'city', 'locality', 'description.en'] as const

export const FIELD_LABELS: Record<string, string> = {
  title: 'Title',
  transaction: 'Sale or rent',
  property_type: 'Property type',
  price_inr: 'Price',
  city: 'City',
  locality: 'Locality',
  media: 'Photos',
  'description.en': 'Description',
}

function getPath(obj: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>((o, k) => (o && typeof o === 'object' ? (o as Record<string, unknown>)[k] : undefined), obj)
}

export function isEmptyField(value: ListingInput, field: string): boolean {
  const v = getPath(value, field)
  if (field === 'media') return !Array.isArray(v) || v.filter((m) => m && (m as { kind?: string }).kind !== 'video').length < 1
  if (Array.isArray(v)) return v.length === 0
  if (typeof v === 'number') return field === 'price_inr' ? !(v > 0) : false
  return v == null || String(v).trim() === ''
}

/** Required fields (plus any the server flagged) that are still empty in the form. Drives the publish block. */
export function missingFields(value: ListingInput, serverMissing: string[] = []): string[] {
  const all = Array.from(new Set<string>([...PUBLISH_REQUIRED, ...serverMissing]))
  return all.filter((f) => isEmptyField(value, f))
}

/**
 * A typo like "85 cr" for "85 lakh" is a 100x error that would go straight to buyers and social pages.
 * Returns a plain-language warning when the price looks implausible for what is being sold, else null.
 * Soft: the agent can confirm an unusual price on purpose (see NewListingFlow).
 */
export function priceSanity(v: ListingInput): string | null {
  const p = v.price_inr
  if (typeof p !== 'number' || !(p > 0)) return null
  if (v.transaction === 'rent') {
    return p < 1500 || p > 1_000_000 ? `A monthly rent of ₹${groupIndian(p)} looks unusual.` : null
  }
  if (p < 100_000) return `A sale price of ₹${groupIndian(p)} looks very low. Did you mean lakh or crore?`
  const flat = !v.property_type || v.property_type === 'apartment'
  const bhk = typeof v.bhk === 'number' ? v.bhk : null
  const tooHighForFlat = flat && (bhk === null ? p > 250_000_000 : bhk <= 3 && p > 100_000_000)
  if (tooHighForFlat || p > 1_000_000_000) {
    const kind = flat && bhk !== null ? `${bhk} BHK apartment` : 'property'
    const hint = p >= 100_000_000 ? ` Did you mean ₹${formatInr(Math.round(p / 100))}?` : ''
    return `₹${formatInr(p)} is very high for a ${kind}.${hint}`
  }
  return null
}

export const LOW_CONFIDENCE = 0.7

export function lowConfidenceFields(confidence: Record<string, number>): string[] {
  return Object.entries(confidence)
    .filter(([, c]) => c < LOW_CONFIDENCE)
    .map(([k]) => k)
}
