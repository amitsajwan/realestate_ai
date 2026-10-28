/**
 * "What to include" under the Add listing box: the facts the AI needs to write a listing with nothing to fix, ticked as the
 * agent types them. Hints only, never a block: the AI reads far looser text than these patterns, and the check step catches gaps.
 */
export interface ListingHint {
  key: 'type' | 'area' | 'price' | 'size' | 'possession'
  label: string
  found: boolean
}

const PATTERNS: Array<[ListingHint['key'], string, RegExp]> = [
  ['type', 'BHK or type', /\b\d(\.\d)?\s*(bhk|rk)\b|\b(studio|plot|shop|office|villa|bungalow|row ?house|penthouse|land)\b/i],
  ['area', 'Area', /\b(in|at|near|opp\.?|behind)\s+[a-z][a-z.]{2,}|\b(baner|aundh|kothrud|wakad|hinjewadi|hinjawadi|kharadi|wagholi|hadapsar|viman nagar|koregaon park|pashan|balewadi|magarpatta|bavdhan|undri|lohegaon|dhanori|ravet|moshi|tathawade|punawale|kondhwa|katraj|sus|mahalunge)\b/i],
  ['price', 'Price', /₹\s*\d|\b\d[\d,.]*\s*(l|lac|lacs|lakh|lakhs|cr|crore|crores|k|thousand)\b|\brs\.?\s*\d/i],
  ['size', 'Size (sq ft)', /\b\d[\d,]*\s*(sq\.?\s*ft|sqft|sft|sq\.?\s*feet|square feet|sq\.?\s*m|carpet)\b/i],
  ['possession', 'Ready or when', /\b(ready|rtm|possession|under construction|u\/c|uc|oc|new launch|resale|20[2-3]\d)\b/i],
]

export function listingHints(text: string): ListingHint[] {
  return PATTERNS.map(([key, label, re]) => ({ key, label, found: re.test(text) }))
}
