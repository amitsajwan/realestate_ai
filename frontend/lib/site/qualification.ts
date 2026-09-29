/** Optional buyer-requirement chips on the public enquiry form (contract: docs/contracts/qualification.md s1-2). Pure, no React. */

export type Timeline = 'now' | '1_3_months' | '3_6_months' | 'exploring'
export type Financing = 'home_loan' | 'own_funds' | 'undecided'
export type BudgetKey = 'under_50l' | '50l_80l' | '80l_1_2cr' | '1_2cr_2cr' | '2cr_plus'

export interface Choice<T extends string | number> { value: T; label: string }
export interface BudgetChoice extends Choice<BudgetKey> { min: number; max: number | null }

const L = 100_000
const CR = 10_000_000

export const BUDGET_CHOICES: BudgetChoice[] = [
  { value: 'under_50l', label: 'Under 50L', min: 0, max: 50 * L },
  { value: '50l_80l', label: '50L-80L', min: 50 * L, max: 80 * L },
  { value: '80l_1_2cr', label: '80L-1.2Cr', min: 80 * L, max: 120 * L },
  { value: '1_2cr_2cr', label: '1.2Cr-2Cr', min: 120 * L, max: 2 * CR },
  { value: '2cr_plus', label: '2Cr+', min: 2 * CR, max: null },
]

export const TIMELINE_CHOICES: Choice<Timeline>[] = [
  { value: 'now', label: 'Now' },
  { value: '1_3_months', label: '1-3 months' },
  { value: '3_6_months', label: '3-6 months' },
  { value: 'exploring', label: 'Just looking' },
]

export const FINANCING_CHOICES: Choice<Financing>[] = [
  { value: 'home_loan', label: 'Home loan' },
  { value: 'own_funds', label: 'Own funds' },
  { value: 'undecided', label: 'Not sure' },
]

/** 4+ is sent as 4. */
export const BHK_CHOICES: Choice<number>[] = [
  { value: 1, label: '1' },
  { value: 2, label: '2' },
  { value: 3, label: '3' },
  { value: 4, label: '4+' },
]

export interface QualificationState {
  bhk: number | null
  budget: BudgetKey | null
  timeline: Timeline | null
  financing: Financing | null
}

export const EMPTY_QUALIFICATION: QualificationState = { bhk: null, budget: null, timeline: null, financing: null }

export interface QualificationFields {
  bhk?: number
  budget_min_inr?: number
  budget_max_inr?: number | null
  timeline?: Timeline
  financing?: Financing
}

/** Tapping the selected chip again clears it. */
export function toggleChoice<T>(current: T | null, picked: T): T | null {
  return current === picked ? null : picked
}

/** Only chosen fields are included, so an untouched block yields {}. */
export function buildQualificationFields(s: QualificationState, opts: { askBhk?: boolean } = {}): QualificationFields {
  const out: QualificationFields = {}
  if (s.bhk != null && opts.askBhk !== false) out.bhk = s.bhk
  const b = BUDGET_CHOICES.find((c) => c.value === s.budget)
  if (b) {
    out.budget_min_inr = b.min
    out.budget_max_inr = b.max
  }
  if (s.timeline) out.timeline = s.timeline
  if (s.financing) out.financing = s.financing
  return out
}

export function hasQualification(f: QualificationFields): boolean {
  return Object.keys(f).length > 0
}
