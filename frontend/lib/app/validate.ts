import type { ListingInput } from './types'

/** Fields the contract requires to publish (docs/contracts/listing.md). 'media' means at least one image. */
export const PUBLISH_REQUIRED = ['title', 'transaction', 'property_type', 'price_inr', 'city', 'locality', 'media', 'description.en'] as const

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

export const LOW_CONFIDENCE = 0.7

export function lowConfidenceFields(confidence: Record<string, number>): string[] {
  return Object.entries(confidence)
    .filter(([, c]) => c < LOW_CONFIDENCE)
    .map(([k]) => k)
}
