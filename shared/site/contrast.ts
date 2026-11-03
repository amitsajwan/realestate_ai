// WCAG 2.x contrast helpers (also used by the preset contrast test).

export function parseHex(hex: string): [number, number, number] {
  let h = hex.trim().replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]
}

export function toHex(rgb: number[]): string {
  return '#' + rgb.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('')
}

export function luminance(hex: string): number {
  const [r, g, b] = parseHex(hex).map((v) => {
    const c = v / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

export function contrast(a: string, b: string): number {
  const la = luminance(a)
  const lb = luminance(b)
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
}

/** Blend `top` over `bottom` with alpha 0..1 (e.g. a dark overlay over a worst-case white photo). */
export function blend(top: string, bottom: string, alpha: number): string {
  const t = parseHex(top)
  const b = parseHex(bottom)
  return toHex(t.map((v, i) => v * alpha + b[i] * (1 - alpha)))
}

/** Mix colour `a` toward colour `b` by `t` (0 = a, 1 = b). */
export function mix(a: string, b: string, t: number): string {
  return blend(b, a, t)
}
