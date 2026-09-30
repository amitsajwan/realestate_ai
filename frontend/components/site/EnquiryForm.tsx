'use client'

import React, { useState } from 'react'
import { normalizeIndianMobile } from '@/lib/site/phone'
import { whatsappLink } from '@/lib/site/links'
import { submitInquiry, trackEvent } from '@/lib/site/tracking'
import {
  BHK_CHOICES, BUDGET_CHOICES, EMPTY_QUALIFICATION, FINANCING_CHOICES, TIMELINE_CHOICES,
  buildQualificationFields, hasQualification, toggleChoice, type Choice, type QualificationFields, type QualificationState,
} from '@/lib/site/qualification'
import { QUALIFY_STRINGS as S } from '@/lib/site/strings'

function ChipGroup<T extends string | number>({ label, options, value, onPick }: {
  label: string; options: Choice<T>[]; value: T | null; onPick: (v: T) => void
}) {
  return (
    <div role="group" aria-label={label}>
      <p className="text-sm font-medium">{label}</p>
      <div className="mt-1 flex flex-wrap gap-2">
        {options.map((o) => {
          const on = value === o.value
          return (
            <button key={String(o.value)} type="button" aria-pressed={on} onClick={() => onPick(o.value)}
              className={'min-h-[44px] min-w-[44px] rounded-full border px-4 text-base ' +
                (on ? 'border-transparent bg-[var(--site-primary)] font-semibold text-[var(--site-on-primary)]' : 'border-slate-300 bg-white text-slate-800')}>
              {o.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

interface Props {
  agentSlug: string
  agentName: string
  agentPhone?: string | null
  listingId?: string
  /** Pre-filled WhatsApp message offered after success. */
  waMessage: string
  id?: string
}

type Errors = { name?: string; phone?: string; consent?: string; form?: string }

export default function EnquiryForm({ agentSlug, agentName, agentPhone, listingId, waMessage, id = 'enquire' }: Props) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [message, setMessage] = useState('')
  const [consent, setConsent] = useState(false)
  const [errors, setErrors] = useState<Errors>({})
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [q, setQ] = useState<QualificationState>(EMPTY_QUALIFICATION)
  const [saved, setSaved] = useState<QualificationFields>({})
  // On a listing page the backend fills BHK from the listing, so we do not ask.
  const askBhk = !listingId
  const pick = <K extends keyof QualificationState>(k: K) => (v: NonNullable<QualificationState[K]>) =>
    setQ((p) => ({ ...p, [k]: toggleChoice(p[k], v) }))

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const errs: Errors = {}
    const n = normalizeIndianMobile(phone)
    if (name.trim().length < 2) errs.name = 'Please enter your name'
    if (!n) errs.phone = 'Enter a valid 10-digit Indian mobile number (starts with 6-9)'
    if (!consent) errs.consent = 'Please tick the box so ' + agentName + ' can contact you'
    setErrors(errs)
    if (Object.keys(errs).length || !n) return
    setBusy(true)
    const extra = buildQualificationFields(q, { askBhk })
    const ok = await submitInquiry(agentSlug, listingId, { name: name.trim(), phone: n, message: message.trim() || undefined, consent, ...extra })
    setBusy(false)
    if (ok) {
      setSaved(extra)
      setDone(true)
    }
    else setErrors({ form: 'Could not send your enquiry. Please try again or use WhatsApp.' })
  }

  if (done) {
    const wa = whatsappLink(agentPhone, waMessage)
    return (
      <section id={id} aria-live="polite" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-center">
        <h2 className="text-xl font-bold text-emerald-900">Thank you, {name.split(' ')[0]}!</h2>
        <p className="mt-1 text-emerald-900">{agentName} will contact you soon.</p>
        {hasQualification(saved) && (
          <p className="mt-2 text-sm text-emerald-900">
            {saved.budget_min_inr != null && saved.timeline ? S.savedNoteBudgetTimeline : S.savedNote}
          </p>
        )}
        {wa && (
          <a href={wa} target="_blank" rel="noopener noreferrer" onClick={() => trackEvent('whatsapp_click', agentSlug, listingId)}
            className="mt-4 inline-flex min-h-[48px] items-center justify-center rounded-xl bg-[#25D366] px-6 font-bold text-[#053b1a] no-underline">
            Continue on WhatsApp
          </a>
        )}
      </section>
    )
  }

  const field = 'mt-1 block min-h-[48px] w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-900'
  return (
    <section id={id} aria-labelledby={id + '-title'} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 id={id + '-title'} className="text-xl font-bold">Enquire with {agentName}</h2>
      <form onSubmit={onSubmit} noValidate className="mt-3 space-y-4">
        <div>
          <label htmlFor={id + '-name'} className="font-medium">Your name</label>
          <input id={id + '-name'} name="name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)}
            aria-invalid={!!errors.name} aria-describedby={errors.name ? id + '-name-err' : undefined} className={field} />
          {errors.name && <p id={id + '-name-err'} role="alert" className="mt-1 text-sm text-red-700">{errors.name}</p>}
        </div>
        <div>
          <label htmlFor={id + '-phone'} className="font-medium">Mobile number</label>
          <input id={id + '-phone'} name="phone" type="tel" inputMode="tel" autoComplete="tel" placeholder="98765 43210"
            value={phone} onChange={(e) => setPhone(e.target.value)}
            aria-invalid={!!errors.phone} aria-describedby={errors.phone ? id + '-phone-err' : undefined} className={field} />
          {errors.phone && <p id={id + '-phone-err'} role="alert" className="mt-1 text-sm text-red-700">{errors.phone}</p>}
        </div>
        <div>
          <label htmlFor={id + '-msg'} className="font-medium">Message <span className="font-normal text-slate-500">(optional)</span></label>
          <textarea id={id + '-msg'} name="message" rows={3} maxLength={1000} value={message} onChange={(e) => setMessage(e.target.value)}
            className={field + ' py-2'} />
        </div>
        <div>
          <label className="flex min-h-[44px] items-start gap-3">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)}
              aria-invalid={!!errors.consent} className="mt-1 h-6 w-6 flex-none" />
            <span className="text-sm">I agree to be contacted by {agentName} about this enquiry.</span>
          </label>
          {errors.consent && <p role="alert" className="mt-1 text-sm text-red-700">{errors.consent}</p>}
        </div>
        <fieldset className="space-y-3 rounded-xl bg-slate-50 p-3">
          <legend className="px-1 text-base font-semibold">{S.title(agentName)}</legend>
          <p className="text-sm text-slate-600">{S.hint}</p>
          {askBhk && <ChipGroup label={S.bhk} options={BHK_CHOICES} value={q.bhk} onPick={pick('bhk')} />}
          <ChipGroup label={S.budget} options={BUDGET_CHOICES} value={q.budget} onPick={pick('budget')} />
          <ChipGroup label={S.timeline} options={TIMELINE_CHOICES} value={q.timeline} onPick={pick('timeline')} />
          <ChipGroup label={S.financing} options={FINANCING_CHOICES} value={q.financing} onPick={pick('financing')} />
        </fieldset>
        {errors.form && <p role="alert"className="text-sm text-red-700">{errors.form}</p>}
        <button type="submit" disabled={busy}
          className="min-h-[52px] w-full rounded-xl bg-[var(--site-primary)] px-6 text-lg font-bold text-[var(--site-on-primary)] disabled:opacity-60">
          {busy ? 'Sending...' : 'Send enquiry'}
        </button>
      </form>
    </section>
  )
}
