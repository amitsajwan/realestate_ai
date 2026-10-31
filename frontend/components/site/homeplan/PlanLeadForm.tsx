'use client'

import React, { useState } from 'react'
import { HOUSE_AGENT_SLUG } from '@/lib/brand'
import { planInquiry, type PlanAnswers } from '@/lib/site/homeplan'
import { normalizeIndianMobile } from '@/lib/site/phone'
import { submitInquiry } from '@/lib/site/tracking'

type Errors = { name?: string; phone?: string; consent?: string; form?: string }

/**
 * The plan's one ask, after the buyer has seen it: send it on WhatsApp with today's prices. Sending makes an Avasetu lead
 * through /t/inquiry with the answers and this plan's link, so the team opens what the buyer saw. `east: false` is the
 * "tell me when you cover my area" version for buyers working elsewhere.
 */
export default function PlanLeadForm({ answers, path, east = true }: { answers: PlanAnswers; path: string; east?: boolean }) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [consent, setConsent] = useState(false)
  const [errors, setErrors] = useState<Errors>({})
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const errs: Errors = {}
    const n = normalizeIndianMobile(phone)
    if (name.trim().length < 2) errs.name = 'Please enter your name'
    if (!n) errs.phone = 'Enter a valid 10-digit Indian mobile number (starts with 6-9)'
    if (!consent) errs.consent = 'Please tick the box so the Avasetu team can contact you'
    setErrors(errs)
    if (Object.keys(errs).length || !n) return
    setBusy(true)
    const ok = await submitInquiry(HOUSE_AGENT_SLUG, undefined, { name: name.trim(), phone: n, consent, ...planInquiry(answers, window.location.origin + path) })
    setBusy(false)
    if (ok) setDone(true)
    else setErrors({ form: 'Could not send. Please try again in a minute.' })
  }

  if (done) {
    return (
      <section aria-live="polite" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-center" data-testid="plan-lead-done">
        <h2 className="text-xl font-bold text-emerald-900">Thank you, {name.trim().split(' ')[0]}!</h2>
        <p className="mt-1 text-emerald-900">
          {east ? 'The Avasetu team will WhatsApp you this plan with today’s prices, and can set up site visits.'
            : 'The Avasetu team has your answers and will tell you when plans cover your area.'}
        </p>
      </section>
    )
  }
  const field = 'mt-1 block min-h-[48px] w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-900 placeholder:text-slate-400'
  return (
    <section aria-labelledby="plan-lead-title" className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="plan-lead">
      <h2 id="plan-lead-title" className="text-xl font-bold text-slate-900">
        {east ? 'Get this plan on WhatsApp, with today’s prices' : 'Tell me when you cover my area'}
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        {east ? 'Published prices go out of date. Our team checks today’s price for each pick and can book the site visits.'
          : 'We will message you once, when our plans cover where you work.'}
      </p>
      <form onSubmit={onSubmit} noValidate className="mt-3 space-y-4">
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
        {errors.form && <p role="alert" className="text-sm text-red-700">{errors.form}</p>}
        <button type="submit" disabled={busy}
          className="min-h-[52px] w-full rounded-xl bg-[var(--site-primary)] px-6 text-lg font-bold text-[var(--site-on-primary)] disabled:opacity-60">
          {busy ? 'Sending...' : east ? 'Send me this plan' : 'Keep me posted'}
        </button>
      </form>
    </section>
  )
}
