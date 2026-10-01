import { contrast, mix } from './contrast'
import { BUTTON_RADIUS, DEFAULT_PRESET, PRESETS, isPresetId, type Preset } from './presets'
import type { AgentBranding } from './types'

const HEX6 = /^#[0-9a-f]{6}$/i

export const DEFAULT_COLORS = { primary: '#102340', secondary: '#0b1a33', accent: '#f0b440' } // PUNE Property navy + gold (= the navy-gold preset)

/** Readable text colour (dark/white) on a hex background. */
export function onColor(hex: string): string {
  let h = hex.replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return (r * 299 + g * 587 + b * 114) / 1000 > 150 ? '#111827' : '#ffffff'
}

/** A custom primary is used only when it is a plain 6-digit hex that keeps white text readable (WCAG AA, 4.5:1). */
export function safeCustomPrimary(v: unknown): string | null {
  if (typeof v !== 'string' || !HEX6.test(v.trim())) return null
  const hex = v.trim().toLowerCase()
  return contrast(hex, '#ffffff') >= 4.5 ? hex : null
}

/** The preset the agent chose (default navy-gold), with his custom primary colour applied when valid. Never trusts stored values blindly. */
export function resolveTheme(branding?: AgentBranding | null): Preset & { custom: boolean } {
  const base = PRESETS[isPresetId(branding?.preset) ? branding!.preset! : DEFAULT_PRESET]
  const custom = safeCustomPrimary(branding?.custom_primary)
  if (!custom) return { ...base, custom: false }
  const light = base.id === 'cream-ink'
  return {
    ...base, custom: true,
    primary: custom,
    secondary: mix(custom, '#000000', 0.4),
    heroFrom: light ? base.heroFrom : mix(custom, '#000000', 0.25),
    heroTo: light ? base.heroTo : custom,
    headerBg: light ? base.headerBg : custom,
  }
}

/** CSS variables for the server-rendered wrapper. Only validated hex values from our own presets (or a contrast-checked custom primary) reach CSS. */
export function themeVars(branding?: AgentBranding | null): Record<string, string> {
  const t = resolveTheme(branding)
  return {
    '--site-primary': t.primary,
    '--site-on-primary': '#ffffff',
    '--site-secondary': t.secondary,
    '--site-on-secondary': '#ffffff',
    '--site-accent': t.accent,
    '--site-on-accent': t.onAccent,
    '--site-accent-text': t.accentText,
    '--site-hero-from': t.heroFrom,
    '--site-hero-to': t.heroTo,
    '--site-hero-fg': t.heroFg,
    '--site-header-bg': t.headerBg,
    '--site-header-fg': t.headerFg,
    '--site-radius': BUTTON_RADIUS[t.button],
  }
}

/** Two-letter monogram for the header when there is no logo ('Deshmukh Realty' -> 'DR'). */
export function monogram(name: string): string {
  const words = name.replace(/[^A-Za-z0-9 ]/g, ' ').split(/\s+/).filter(Boolean)
  if (!words.length) return 'P'
  return (words.length === 1 ? words[0].slice(0, 2) : words[0][0] + words[1][0]).toUpperCase()
}

const IMG = /^(?:https?:\/\/[^/\s]+)?\/uploads\/images\/[A-Za-z0-9][A-Za-z0-9._-]{0,200}$/
/** Logo/banner are rendered only when they are images we stored ourselves (same rule as the API). */
export function safeImage(v: unknown): string | null {
  return typeof v === 'string' && IMG.test(v.trim()) ? v.trim() : null
}

export const MAHARERA_URL = 'https://maharera.maharashtra.gov.in'
const RERA = /^A\d{6,18}$/
export function safeRera(v: unknown): string | null {
  return typeof v === 'string' && RERA.test(v.trim()) ? v.trim() : null
}

/** What the public site calls the agent: his business name when he set one, else his own name. */
export function displayName(agent: { agent_name: string; branding_data?: AgentBranding | null }): string {
  return (agent.branding_data?.business_name || '').trim() || agent.agent_name
}
