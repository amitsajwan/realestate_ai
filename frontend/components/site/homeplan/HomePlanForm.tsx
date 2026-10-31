'use client'

import React, { useState } from 'react'
import { ChipGroup } from '@/components/site/EnquiryForm'
import { HOUSE_AGENT_SLUG } from '@/lib/brand'
import { BHKS, BUDGETS, MOVE_INS } from '@/lib/site/finder'
import { ELDERS, KIDS, WORK, complete, planInquiry, toPlanSearch, type PlanAnswers } from '@/lib/site/homeplan'
import { normalizeIndianMobile } from '@/lib/site/phone'
import { submitInquiry } from '@/lib/site/tracking'

export const RESULT_PATH = '/home-plan/result'

type Errors = { answers?: string; name?: string; phone?: string; consent?: string; form?: string }

/**
 * The six questions as taps, then name, mobile and consent. Sending makes the enquiry (an Avasetu lead with the answers and the
 * plan's link, through the same /t/inquiry as every form) and opens the plan. `start` carries answers from an "edit" link.
 */
export default function HomePlanForm({ start = {} }: { start?: PlanAnswers }) {
  const [a, setA] = useState<PlanAnswers>(start)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [consent, setConsent] = useState(false)
  const [errors, setErrors] = useState<Errors>({})
  const [busy, setBusy] = useState(false)
  const set = <K extends keyof PlanAnswers>(k: K) => (v: PlanAnswers[K]) => setA((p) => ({ ...p, [k]: p[k] === v ? undefined : v }))

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const errs: Errors = {}
    const n = normalizeIndianMobile(phone)
    if (!complete(a)) errs.answers = 'Please pick where you work, your budget and the size of home'
    if (name.trim().length < 2) errs.name = 'Please enter your name'
    if (!n) errs.phone = 'Enter a valid 10-digit Indian mobile number (starts with 6-9)'
    if (!consent) errs.consent = 'Please tick the box so the Avasetu team can send you the plan'
    setErrors(errs)
    if (Object.keys(errs).length || !n) return
    setBusy(true)
    const path = RESULT_PATH + toPlanSearch(a)
    const ok = await submitInquiry(HOUSE_AGENT_SLUG, undefined, { name: name.trim(), phone: n, consent, ...planInquiry(a, window.location.origin + path) })
    setBusy(false)
    if (ok) window.location.assign(path)
    else setErrors({ form: 'Could not send your answers. Please try again in a minute.' })
  }

  const field = 'mt-1 block min-h-[48px] w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-900 placeholder:text-slate-400'
  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5" data-testid="home-plan-form">
      <ChipGroup label="1. Where do you (or the main earner) work?" options={WORK.map((w) => ({ value: w.key, label: w.label }))}
        value={a.work ?? null} onPick={set('work')} />
      <ChipGroup label="2. Your budget" options={BUDGETS.map((b) => ({ value: b.key, label: b.label }))} value={a.budget ?? null} onPick={set('budget')} />
      <ChipGroup label="3. Size of home" options={BHKS.map((b) => ({ value: b.key, label: b.label }))} value={a.bhk ?? null} onPick={set('bhk')} />
      <ChipGroup label="4. When do you want to move in? (leave empty for any time)" options={MOVE_INS.map((m) => ({ value: m.key, label: m.label }))}
        value={a.movein ?? null} onPick={set('movein')} />
      <ChipGroup label="5. Children at home" options={KIDS.map((k) => ({ value: k.key, label: k.label }))} value={a.kids ?? null} onPick={set('kids')} />
      <ChipGroup label="6. Will parents live with you?" options={ELDERS.map((x) => ({ value: x.key, label: x.label }))}
        value={a.elders == null ? null : a.elders ? '1' : '0'} onPick={(v) => setA((p) => ({ ...p, elders: p.elders === (v === '1') ? undefined : v === '1' }))} />
      {errors.answers && <p role="alert" className="text-sm text-red-700">{errors.answers}</p>}

      <div className="space-y-4 rounded-xl bg-slate-50 p-4">
        <p className="text-sm text-slate-700">Where should we send your plan? We send it on WhatsApp and call only about this plan.</p>
        <div>
          <label htmlFor="plan-name" className="font-medium">Your name</label>
          <input id="plan-name" name="name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)}
            aria-invalid={!!errors.name} aria-describedby={errors.name ? 'plan-name-err' : undefined} className={field} />
          {errors.name && <p id="plan-name-err" role="alert" className="mt-1 text-sm text-red-700">{errors.name}</p>}
        </div>
        <div>
          <label htmlFor="plan-phone" className="font-medium">Mobile number</label>
          <input id="plan-phone" name="phone" type="tel" inputMode="tel" autoComplete="tel" placeholder="98765 43210"
            value={phone} onChange={(e) => setPhone(e.target.value)}
            aria-invalid={!!errors.phone} aria-describedby={errors.phone ? 'plan-phone-err' : undefined} className={field} />
          {errors.phone && <p id="plan-phone-err" role="alert" className="mt-1 text-sm text-red-700">{errors.phone}</p>}
        </div>
        <div>
          {/* the buyer ticks this themselves: a pre-ticked box is not valid consent under the DPDP Act */}
          <label className="flex min-h-[44px] items-center gap-3">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)}
              aria-invalid={!!errors.consent} aria-describedby={errors.consent ? 'plan-consent-err' : undefined} className="h-6 w-6 flex-none" />
            <span className="text-sm text-slate-700">I agree to be contacted by the Avasetu team about this plan.</span>
          </label>
          {errors.consent && <p id="plan-consent-err" role="alert" className="mt-1 text-sm text-red-700">{errors.consent}</p>}
        </div>
      </div>
      {errors.form && <p role="alert" className="text-sm text-red-700">{errors.form}</p>}
      <button type="submit" disabled={busy}
        className="min-h-[52px] w-full rounded-xl bg-[var(--site-primary)] px-6 text-lg font-bold text-[var(--site-on-primary)] disabled:opacity-60">
        {busy ? 'Making your plan...' : 'Show my home plan'}
      </button>
    </form>
  )
}
