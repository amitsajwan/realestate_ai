import {
  BHK_CHOICES, BUDGET_CHOICES, EMPTY_QUALIFICATION, FINANCING_CHOICES, TIMELINE_CHOICES,
  buildQualificationFields, hasQualification, toggleChoice,
} from '@/lib/site/qualification'

describe('qualification mapping', () => {
  it('maps every budget choice to min/max rupees', () => {
    const m = Object.fromEntries(BUDGET_CHOICES.map((b) => [b.value, [b.min, b.max]]))
    expect(m).toEqual({
      under_50l: [0, 5_000_000],
      '50l_80l': [5_000_000, 8_000_000],
      '80l_1_2cr': [8_000_000, 12_000_000],
      '1_2cr_2cr': [12_000_000, 20_000_000],
      '2cr_plus': [20_000_000, null],
    })
  })

  it('uses contract enum values', () => {
    expect(TIMELINE_CHOICES.map((c) => c.value)).toEqual(['now', '1_3_months', '3_6_months', 'exploring'])
    expect(FINANCING_CHOICES.map((c) => c.value)).toEqual(['home_loan', 'own_funds', 'undecided'])
    expect(BHK_CHOICES.map((c) => c.value)).toEqual([1, 2, 3, 4])
  })

  it('omits unset fields', () => {
    expect(buildQualificationFields(EMPTY_QUALIFICATION)).toEqual({})
    expect(hasQualification({})).toBe(false)
    expect(buildQualificationFields({ ...EMPTY_QUALIFICATION, timeline: 'now' })).toEqual({ timeline: 'now' })
  })

  it('builds open-ended budget with null max', () => {
    expect(buildQualificationFields({ ...EMPTY_QUALIFICATION, budget: '2cr_plus' })).toEqual({ budget_min_inr: 20_000_000, budget_max_inr: null })
  })

  it('drops bhk when not asked', () => {
    const s = { ...EMPTY_QUALIFICATION, bhk: 3 }
    expect(buildQualificationFields(s)).toEqual({ bhk: 3 })
    expect(buildQualificationFields(s, { askBhk: false })).toEqual({})
  })

  it('toggling the same choice clears it', () => {
    expect(toggleChoice<string>(null, 'a')).toBe('a')
    expect(toggleChoice<string>('a', 'a')).toBeNull()
    expect(toggleChoice<string>('a', 'b')).toBe('b')
  })
})
