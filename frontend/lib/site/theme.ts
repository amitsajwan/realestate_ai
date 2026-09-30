import type { AgentBranding } from './types'

const HEX = /^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i
const pick = (v: string | undefined, fallback: string) => (v && HEX.test(v.trim()) ? v.trim() : fallback)

export const DEFAULT_COLORS = { primary: '#102340', secondary: '#0b1a33', accent: '#f0b440' } // PUNE Property navy + gold

/** Readable text colour (dark/white) on a hex background. */
export function onColor(hex: string): string {
  let h = hex.replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return (r * 299 + g * 587 + b * 114) / 1000 > 150 ? '#111827' : '#ffffff'
}

/** CSS variables for the server-rendered wrapper. Values are validated hex only (no CSS injection). */
export function themeVars(branding?: AgentBranding | null): Record<string, string> {
  void branding // one brand for the whole pilot: stored per-agent colours are ignored until agents can choose their own
  const primary = pick(undefined, DEFAULT_COLORS.primary)
  const secondary = pick(undefined, DEFAULT_COLORS.secondary)
  const accent = pick(undefined, DEFAULT_COLORS.accent)
  return {
    '--site-primary': primary,
    '--site-on-primary': onColor(primary),
    '--site-secondary': secondary,
    '--site-on-secondary': onColor(secondary),
    '--site-accent': accent,
  }
}
