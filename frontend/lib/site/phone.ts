/** Normalize an Indian mobile to 10 digits, or null if invalid (10 digits starting 6-9; +91/91/0 prefix and spaces allowed). */
export function normalizeIndianMobile(input: string): string | null {
  if (!input) return null
  let d = input.replace(/[\s\-().]/g, '')
  if (d.indexOf('+91') === 0) d = d.slice(3)
  else if (/^91\d{10}$/.test(d)) d = d.slice(2)
  else if (/^0\d{10}$/.test(d)) d = d.slice(1)
  return /^[6-9]\d{9}$/.test(d) ? d : null
}

export const isValidIndianMobile = (input: string): boolean => normalizeIndianMobile(input) !== null

/** Digits for wa.me / tel: links with country code: "919876543210". Null if not a valid Indian mobile. */
export function waNumber(input?: string | null): string | null {
  const n = normalizeIndianMobile(input || '')
  return n ? '91' + n : null
}
