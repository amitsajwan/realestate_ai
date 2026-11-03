// The six designed brand presets an agent can pick. Mirrors backend/app/modules/onboarding/branding.py (PRESETS);
// a jest test pins primary/secondary/accent against the backend list and checks WCAG AA contrast for every text/background pair.

export type PresetId = 'navy-gold' | 'emerald' | 'terracotta' | 'royal-purple' | 'slate-teal' | 'cream-ink'
export type HeroArt = 'skyline' | 'arcs' | 'sun' | 'diagonal' | 'grid' | 'paper'
export type ButtonStyle = 'pill' | 'rounded' | 'square'

export interface Preset {
  id: PresetId
  label: string
  blurb: string
  primary: string // buttons, prices, links on white; white text sits on it
  secondary: string // footer; white text sits on it
  accent: string // highlights on dark surfaces and the main hero button fill
  onAccent: string // text on an accent fill
  accentText: string // accent-family colour that is readable as TEXT on white
  heroFrom: string
  heroTo: string
  heroFg: string // text colour on the hero stops (when there is no banner)
  headerBg: string
  headerFg: string
  art: HeroArt
  button: ButtonStyle
}

export const PRESETS: Record<PresetId, Preset> = {
  'navy-gold': {
    id: 'navy-gold', label: 'Navy and gold', blurb: 'Classic, trusted',
    primary: '#102340', secondary: '#0b1a33', accent: '#f0b440', onAccent: '#18202c', accentText: '#8a5a00',
    heroFrom: '#102340', heroTo: '#183a5d', heroFg: '#ffffff', headerBg: '#102340', headerFg: '#ffffff', art: 'skyline', button: 'pill',
  },
  emerald: {
    id: 'emerald', label: 'Emerald', blurb: 'Fresh, family homes',
    primary: '#0b5d46', secondary: '#083f31', accent: '#f4c95d', onAccent: '#1d2a1f', accentText: '#7a5a00',
    heroFrom: '#0a4f3b', heroTo: '#15795c', heroFg: '#ffffff', headerBg: '#0b5d46', headerFg: '#ffffff', art: 'arcs', button: 'rounded',
  },
  terracotta: {
    id: 'terracotta', label: 'Terracotta', blurb: 'Warm, local',
    primary: '#9c3d1f', secondary: '#6e2812', accent: '#f2c46d', onAccent: '#2a160c', accentText: '#7a4a00',
    heroFrom: '#8a3419', heroTo: '#b04a28', heroFg: '#ffffff', headerBg: '#9c3d1f', headerFg: '#ffffff', art: 'sun', button: 'pill',
  },
  'royal-purple': {
    id: 'royal-purple', label: 'Royal purple', blurb: 'Premium, bold',
    primary: '#4a2a82', secondary: '#321b5c', accent: '#f0c75e', onAccent: '#241540', accentText: '#7a5600',
    heroFrom: '#3b2068', heroTo: '#6a3fb5', heroFg: '#ffffff', headerBg: '#4a2a82', headerFg: '#ffffff', art: 'diagonal', button: 'square',
  },
  'slate-teal': {
    id: 'slate-teal', label: 'Slate and teal', blurb: 'Modern, calm',
    primary: '#26414d', secondary: '#182b34', accent: '#5fd0c2', onAccent: '#0b2a2a', accentText: '#0b6b61',
    heroFrom: '#1c323c', heroTo: '#1f6f73', heroFg: '#ffffff', headerBg: '#26414d', headerFg: '#ffffff', art: 'grid', button: 'rounded',
  },
  'cream-ink': {
    id: 'cream-ink', label: 'Cream and ink', blurb: 'Quiet, editorial',
    primary: '#2b2118', secondary: '#1c150f', accent: '#c8963e', onAccent: '#1c150f', accentText: '#7a5518',
    heroFrom: '#f8f1e4', heroTo: '#eadcc0', heroFg: '#2b2118', headerBg: '#f8f1e4', headerFg: '#2b2118', art: 'paper', button: 'square',
  },
}

export const PRESET_IDS = Object.keys(PRESETS) as PresetId[]
export const DEFAULT_PRESET: PresetId = 'navy-gold'

export function isPresetId(v: unknown): v is PresetId {
  return typeof v === 'string' && Object.prototype.hasOwnProperty.call(PRESETS, v)
}

export const BUTTON_RADIUS: Record<ButtonStyle, string> = { pill: '9999px', rounded: '14px', square: '5px' }

/** Dark overlay laid over a banner photo so white text stays readable on any picture (worst case: a white photo). */
export const BANNER_OVERLAY = { from: 'rgba(8,12,20,0.62)', to: 'rgba(8,12,20,0.86)', solid: '#080c14', minAlpha: 0.62 }
