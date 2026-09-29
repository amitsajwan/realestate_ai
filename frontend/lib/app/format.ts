/** INR formatting/parsing, phone normalisation and relative time. Money is always integer rupees. */

const LAKH = 100_000
const CRORE = 10_000_000

function trim(n: number, digits: number): string {
  return String(Number(n.toFixed(digits)))
}

/** 8500000 -> "85 L", 12500000 -> "1.25 Cr", 45000 -> "45,000". Contract style. */
export function formatInr(rupees: number | null | undefined): string {
  if (rupees == null || !isFinite(rupees)) return ''
  const n = Math.round(rupees)
  if (n >= CRORE) return `${trim(n / CRORE, 2)} Cr`
  if (n >= LAKH) return `${trim(n / LAKH, 2)} L`
  return groupIndian(n)
}

/** "₹85 L" / "₹45,000/mo" helper for cards. */
export function formatPrice(rupees: number | null | undefined, rent = false): string {
  const s = formatInr(rupees)
  return s ? `₹${s}${rent ? '/mo' : ''}` : ''
}

/** Indian digit grouping: 8500000 -> "85,00,000". */
export function groupIndian(n: number): string {
  const s = String(Math.abs(Math.trunc(n)))
  const sign = n < 0 ? '-' : ''
  if (s.length <= 3) return sign + s
  const last3 = s.slice(-3)
  const rest = s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',')
  return `${sign}${rest},${last3}`
}

const UNITS: Array<[RegExp, number]> = [
  [/^(cr|crore|crores)$/, CRORE],
  [/^(l|lac|lacs|lakh|lakhs|lk)$/, LAKH],
  [/^(k|thousand)$/, 1000],
]

/**
 * Parse free-typed money into integer rupees.
 * '85 lakh' '1.2cr' '₹85,00,000' '85l' '50k' '8500000' -> integers. Returns null when not understood.
 * A bare number is taken as rupees.
 */
export function parseInr(input: string | number | null | undefined): number | null {
  if (input == null) return null
  if (typeof input === 'number') return isFinite(input) ? Math.round(input) : null
  const s = input.toLowerCase().replace(/[₹,]/g, '').replace(/\brs\.?|\binr\b/g, '').trim()
  if (!s) return null
  const m = s.match(/^(\d+(?:\.\d+)?)\s*([a-z]*)$/)
  if (!m) return null
  const value = parseFloat(m[1])
  if (!m[2]) return Math.round(value)
  const unit = UNITS.find(([re]) => re.test(m[2]))
  return unit ? Math.round(value * unit[1]) : null
}

/** Normalise an Indian mobile to +91XXXXXXXXXX, or null when invalid (mirrors backend phone.py). */
export function normalizePhone(raw: string): string | null {
  let digits = (raw || '').replace(/\D/g, '')
  if (digits.length === 12 && digits.startsWith('91')) digits = digits.slice(2)
  else if (digits.length === 11 && digits.startsWith('0')) digits = digits.slice(1)
  return /^[6-9]\d{9}$/.test(digits) ? `+91${digits}` : null
}

/** '+919876543210' -> '+91 98765 43210' */
export function displayPhone(phone: string): string {
  const p = normalizePhone(phone)
  return p ? `+91 ${p.slice(3, 8)} ${p.slice(8)}` : phone
}

/** Digits only, for wa.me links: '+919876543210' -> '919876543210'. */
export function waDigits(phone: string): string {
  const p = normalizePhone(phone)
  return (p ?? phone).replace(/\D/g, '')
}

/** "2h ago", "3d ago", "just now". */
export function timeAgo(iso: string, now: Date = new Date()): string {
  // The backend sends naive UTC datetimes; treat a missing zone as UTC.
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(iso)
  const then = new Date(hasZone ? iso : iso + 'Z').getTime()
  if (isNaN(then)) return ''
  const sec = Math.max(0, Math.round((now.getTime() - then) / 1000))
  if (sec < 60) return 'just now'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const d = Math.floor(hr / 24)
  if (d < 30) return `${d}d ago`
  return `${Math.floor(d / 30)}mo ago`
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}
