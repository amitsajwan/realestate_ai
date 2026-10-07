import { blend, contrast } from '@/lib/site/contrast'
import { BANNER_OVERLAY, PRESETS, PRESET_IDS } from '@/lib/site/presets'
import { onColor, resolveTheme, safeCustomPrimary, themeVars } from '@/lib/site/theme'

const AA = 4.5
const WHITE = '#ffffff'

describe('brand presets meet WCAG AA', () => {
  it('has the six agreed presets', () => {
    expect(PRESET_IDS.sort()).toEqual(['cream-ink', 'emerald', 'navy-gold', 'royal-purple', 'slate-teal', 'terracotta'])
  })

  it.each(PRESET_IDS)('%s: every text/background pair is at least 4.5:1', (id) => {
    const p = PRESETS[id]
    const pairs: Array<[string, string, string]> = [
      ['white on primary (buttons, chips)', WHITE, p.primary],
      ['white on secondary (footer)', WHITE, p.secondary],
      ['hero text on hero start', p.heroFg, p.heroFrom],
      ['hero text on hero end', p.heroFg, p.heroTo],
      ['header text on header', p.headerFg, p.headerBg],
      ['text on accent fill', p.onAccent, p.accent],
      ['accent text on white', p.accentText, WHITE],
      ['accent on footer (secondary)', p.accent, p.secondary],
    ]
    for (const [label, fg, bg] of pairs) {
      expect({ label, ratio: contrast(fg, bg) >= AA }).toEqual({ label, ratio: true })
    }
  })

  it.each(PRESET_IDS)('%s: the main hero button stands out from the hero (3:1)', (id) => {
    const p = PRESETS[id]
    const fill = p.id === 'cream-ink' ? p.primary : p.accent // light hero: ink button; dark hero: accent button
    expect(contrast(fill, p.heroFrom)).toBeGreaterThanOrEqual(3)
    expect(contrast(fill, p.heroTo)).toBeGreaterThanOrEqual(3)
  })

  it('white text over the banner overlay stays readable even on a pure white photo', () => {
    for (const alpha of [BANNER_OVERLAY.minAlpha, 0.86]) {
      expect(contrast(WHITE, blend(BANNER_OVERLAY.solid, WHITE, alpha))).toBeGreaterThanOrEqual(AA)
    }
    expect(BANNER_OVERLAY.from).toContain('0.62')
  })
})

describe('custom primary colour', () => {
  it('accepts dark colours and rejects ones that cannot carry white text', () => {
    expect(safeCustomPrimary('#1A2B5C')).toBe('#1a2b5c')
    expect(safeCustomPrimary('#ffff00')).toBeNull()
    expect(safeCustomPrimary('#fff')).toBeNull()
    expect(safeCustomPrimary('red;}')).toBeNull()
    expect(safeCustomPrimary(undefined)).toBeNull()
  })

  it('every derived colour from a borderline custom primary keeps white text at AA', () => {
    for (const id of PRESET_IDS) {
      const t = resolveTheme({ preset: id, custom_primary: '#767676' }) // lightest grey that still passes 4.5:1 on white
      expect(t.custom).toBe(true)
      for (const bg of [t.primary, t.secondary]) expect(contrast(WHITE, bg)).toBeGreaterThanOrEqual(AA)
      if (id !== 'cream-ink') for (const bg of [t.heroFrom, t.heroTo, t.headerBg]) expect(contrast(WHITE, bg)).toBeGreaterThanOrEqual(AA)
    }
  })

  it('ignores a too-light custom colour and unknown presets (falls back to navy-gold)', () => {
    const v = themeVars({ preset: 'neon' as never, custom_primary: '#ffff00' })
    expect(v['--site-primary']).toBe('#102340')
    expect(v['--site-accent']).toBe('#f0b440')
  })

  it('an agent with no branding keeps the Avasetu navy and gold', () => {
    const v = themeVars(null)
    expect(v['--site-primary']).toBe('#102340')
    expect(v['--site-secondary']).toBe('#0b1a33')
    expect(onColor('#102340')).toBe('#ffffff')
  })
})
