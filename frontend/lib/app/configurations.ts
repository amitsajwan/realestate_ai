import { parseInr } from './format'
import type { Configuration } from './types'

/** A builder's price sheet pasted as text ("2 BHK Apartments Area 730 Sq. Ft. Price ₹ 1.20 Cr* View Details 3 BHK ...") as
 *  rows: each "N BHK" starts a row, which takes the first area (sq ft) and the first price (Cr, Lakh, L) after it. */
export function parsePriceSheet(text: string): Configuration[] {
  const s = text.replace(/\s+/g, ' ')
  const starts = Array.from(s.matchAll(/(\d(?:\.5)?)\s*BHK/gi))
  const out: Configuration[] = []
  starts.forEach((m, i) => {
    const part = s.slice(m.index! + m[0].length, i + 1 < starts.length ? starts[i + 1].index : undefined)
    const area = part.match(/(\d[\d,]{2,5})\s*(?:sq\.?\s*ft|sqft|sq\.?\s*feet)/i)
    const price = part.match(/(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(cr(?:ore)?s?|lakhs?|lacs?|l)\b/i)
    const row: Configuration = { bhk: parseFloat(m[1]) }
    if (area) row.carpet_sqft = parseInt(area[1].replace(/,/g, ''), 10)
    if (price) row.price_inr = parseInr(`${price[1]} ${price[2]}`)
    if (row.carpet_sqft || row.price_inr) out.push(row)
  })
  return out
}

/** The smallest home and the lowest price of the table: the listing's own BHK, carpet and "from" price. */
export function fromRows(rows: Configuration[]): { bhk?: number; carpet_sqft?: number; price_inr?: number } {
  const priced = rows.filter((r) => r.price_inr)
  const low = priced.length ? priced.reduce((a, b) => ((a.price_inr ?? 0) <= (b.price_inr ?? 0) ? a : b)) : rows[0]
  if (!low) return {}
  return { bhk: Math.min(...rows.map((r) => r.bhk)), carpet_sqft: low.carpet_sqft ?? undefined, price_inr: low.price_inr ?? undefined }
}
