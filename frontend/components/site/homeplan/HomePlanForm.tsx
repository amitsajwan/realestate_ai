'use client'

import React, { useState } from 'react'
import { ChipGroup } from '@/components/site/EnquiryForm'
import { BHKS, BUDGETS, MOVE_INS } from '@/lib/site/finder'
import { ELDERS, KIDS, WORK, complete, type PlanAnswers } from '@/lib/site/homeplan'

export const RESULT_PATH = '/home-plan/result'

/**
 * The six questions as taps. The plan comes first and asks for nothing (owner 2026-10-31: "show the plan before asking for
 * phone number"): the form is a plain GET to the plan with the answers in the address, and the plan page offers to send it on
 * WhatsApp. `start` carries answers from an "edit" link.
 */
export default function HomePlanForm({ start = {} }: { start?: PlanAnswers }) {
  const [a, setA] = useState<PlanAnswers>(start)
  const [error, setError] = useState(false)
  const set = <K extends keyof PlanAnswers>(k: K) => (v: PlanAnswers[K]) => setA((p) => ({ ...p, [k]: p[k] === v ? undefined : v }))
  const hidden: [string, string | undefined][] = [
    ['work', a.work], ['budget', a.budget], ['bhk', a.bhk], ['movein', a.movein], ['kids', a.kids],
    ['elders', a.elders == null ? undefined : a.elders ? '1' : '0'],
  ]
  const onSubmit = (e: React.FormEvent) => {
    if (complete(a)) return
    e.preventDefault()
    setError(true)
  }
  return (
    <form action={RESULT_PATH} method="get" onSubmit={onSubmit} noValidate className="space-y-5" data-testid="home-plan-form">
      {hidden.filter(([, v]) => v).map(([k, v]) => <input key={k} type="hidden" name={k} value={v} />)}
      <ChipGroup label="1. Where do you (or the main earner) work?" options={WORK.map((w) => ({ value: w.key, label: w.label }))}
        value={a.work ?? null} onPick={set('work')} />
      <ChipGroup label="2. Your budget" options={BUDGETS.map((b) => ({ value: b.key, label: b.label }))} value={a.budget ?? null} onPick={set('budget')} />
      <ChipGroup label="3. Size of home" options={BHKS.map((b) => ({ value: b.key, label: b.label }))} value={a.bhk ?? null} onPick={set('bhk')} />
      <ChipGroup label="4. When do you want to move in? (leave empty for any time)" options={MOVE_INS.map((m) => ({ value: m.key, label: m.label }))}
        value={a.movein ?? null} onPick={set('movein')} />
      <ChipGroup label="5. Children at home" options={KIDS.map((k) => ({ value: k.key, label: k.label }))} value={a.kids ?? null} onPick={set('kids')} />
      <ChipGroup label="6. Will parents live with you?" options={ELDERS.map((x) => ({ value: x.key, label: x.label }))}
        value={a.elders == null ? null : a.elders ? '1' : '0'} onPick={(v) => setA((p) => ({ ...p, elders: p.elders === (v === '1') ? undefined : v === '1' }))} />
      {error && !complete(a) && <p role="alert" className="text-sm text-red-700">Please pick where you work, your budget and the size of home</p>}
      <button type="submit"
        className="min-h-[52px] w-full rounded-xl bg-[var(--site-primary)] px-6 text-lg font-bold text-[var(--site-on-primary)]">
        Show my home plan
      </button>
      <p className="text-center text-sm text-slate-600">Free, and no phone number needed to see it.</p>
    </form>
  )
}
