'use client'

import React, { useEffect, useState } from 'react'
import { normalizeIndianMobile } from '@/lib/site/phone'
import { whatsappLink } from '@/lib/site/links'
import { submitInquiry, trackEvent } from '@/lib/site/tracking'
import {
  BHK_CHOICES, BUDGET_CHOICES, EMPTY_QUALIFICATION, FINANCING_CHOICES, TIMELINE_CHOICES,
  buildQualificationFields, hasQualification, toggleChoice, type Choice, type QualificationFields, type QualificationState,
} from '@/lib/site/qualification'
import { QUALIFY_STRINGS as S, contactName, contactNameStart } from '@/lib/site/strings'

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

/** One ask a form can carry (a project page's price sheet or its site visit). The buyer picks one in the form, and a link to
 *  `#<anchor>` opens the form on it, so two buttons up the page need one form, not two copies of it. */
export interface EnquiryChoice {
  label: string
  anchor: string
  title: string
  topic: string
  waMessage: string
  submitLabel: string
}

interface Props {
  agentSlug: string
  agentName: string
  agentPhone?: string | null
  listingId?: string
  /** What the enquiry is about when there is no listing (a builder project): sent at the start of the message. */
  topic?: string
  /** Pre-filled WhatsApp message offered after success. */
  waMessage: string
  id?: string
  /** The heading. Project pages name their one action here ("Get the price sheet and floor plans for ..."). */
  title?: string
  /** A line under the heading: who gets back to the buyer, and that the number is not shared. */
  note?: string
  /** The send button's words. Project pages repeat their one action. */
  submitLabel?: string
  /** When set, the form asks which of these the buyer wants, and the heading, topic, WhatsApp message and button follow the pick. */
  choices?: EnquiryChoice[]
}

type Errors = { name?: string; phone?: string; consent?: string; form?: string }

export default function EnquiryForm({ agentSlug, agentName, agentPhone, listingId, topic: baseTopic, waMessage: baseWa, id = 'enquire',
  title: baseTitle, note, submitLabel: baseSubmit = 'Send enquiry', choices }: Props) {
  const [picked, setPicked] = useState(choices?.[0]?.anchor)
  const choice = choices?.find((c) => c.anchor === picked)
  const topic = choice?.topic ?? baseTopic
  const waMessage = choice?.waMessage ?? baseWa
  const title = choice?.title ?? baseTitle
  const submitLabel = choice?.submitLabel ?? baseSubmit
  // a link to one of the choices' anchors (the hero's "Book a site visit") switches the form to it; clicks are watched as well as
  // the hash, because clicking a link to the hash already in the address bar fires no hashchange
  useEffect(() => {
    if (!choices?.length) return
    const anchors = choices.map((c) => c.anchor)
    const fromHash = () => {
      const h = window.location.hash.slice(1)
      if (anchors.includes(h)) setPicked(h)
    }
    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.('a[href^="#"]')
      const h = a?.getAttribute('href')?.slice(1)
      if (h && anchors.includes(h)) setPicked(h)
    }
    fromHash()
    window.addEventListener('hashchange', fromHash)
    document.addEventListener('click', onClick)
    return () => {
      window.removeEventListener('hashchange', fromHash)
      document.removeEventListener('click', onClick)
    }
  }, [choices])
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
  // the house account reads as "the Avasetu team" in every line the buyer sees (owner rule: no personal names to leads)
  const who = contactName(agentName)
  const pick = <K extends keyof QualificationState>(k: K) => (v: NonNullable<QualificationState[K]>) =>
    setQ((p) => ({ ...p, [k]: toggleChoice(p[k], v) }))

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const errs: Errors = {}
    const n = normalizeIndianMobile(phone)
    if (name.trim().length < 2) errs.name = 'Please enter your name'
    if (!n) errs.phone = 'Enter a valid 10-digit Indian mobile number (starts with 6-9)'
    if (!consent) errs.consent = 'Please tick the box so ' + who + ' can contact you'
    setErrors(errs)
    if (Object.keys(errs).length || !n) return
    setBusy(true)
    const extra = buildQualificationFields(q, { askBhk })
    const ok = await submitInquiry(agentSlug, listingId, { name: name.trim(), phone: n, message: [topic ? 'About ' + topic : '', message.trim()].filter(Boolean).join(': ') || undefined, consent, ...extra })
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
      <section id={id} aria-live="polite" className="scroll-mt-20 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-center">
        <h2 className="text-xl font-bold text-emerald-900">Thank you, {name.split(' ')[0]}!</h2>
        <p className="mt-1 text-emerald-900">{contactNameStart(agentName)} will call or WhatsApp you soon.</p>
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

  // the placeholder is lighter than typed text so an empty field does not look filled in
  const field = 'mt-1 block min-h-[48px] w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-900 placeholder:text-slate-400'
  // One section, one heading and one id: pages link to `#enquire`, and the phone's bottom bar hides while it is on screen.
  return (
    <section id={id} aria-labelledby={id + '-title'} className="scroll-mt-20 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      {choices?.filter((c) => c.anchor !== id).map((c) => <span key={c.anchor} id={c.anchor} className="block scroll-mt-20" />)}
      <h2 id={id + '-title'} className="text-xl font-bold">{title ?? 'Enquire with ' + agentName}</h2>
      {note && <p className="mt-1 text-sm text-slate-600">{note}</p>}
      <form onSubmit={onSubmit} noValidate className="mt-3 space-y-4">
        {choices && choices.length > 1 && (
          <ChipGroup label={S.want} options={choices.map((c) => ({ value: c.anchor, label: c.label }))} value={picked ?? null} onPick={setPicked} />
        )}
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
        {askBhk && <ChipGroup label={S.bhk} options={BHK_CHOICES} value={q.bhk} onPick={pick('bhk')} />}
        <div>
          {/* the buyer ticks this themselves: a pre-ticked box is not valid consent under the DPDP Act */}
          <label className="flex min-h-[44px] items-center gap-3">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)}
              aria-invalid={!!errors.consent} aria-describedby={errors.consent ? id + '-consent-err' : undefined} className="h-6 w-6 flex-none" />
            <span className="text-sm text-slate-700">I agree to be contacted by {who} about this enquiry.</span>
          </label>
          {errors.consent && <p id={id + '-consent-err'} role="alert" className="mt-1 text-sm text-red-700">{errors.consent}</p>}
        </div>
        {/* Closed at first: on a phone these chips took two more screens before the send button. Whatever is picked or typed in
            here is still sent with the enquiry, exactly as before. */}
        <details className="group rounded-xl bg-slate-50">
          <summary className="flex min-h-[48px] cursor-pointer list-none items-center justify-between gap-2 px-3 font-semibold text-slate-900 [&::-webkit-details-marker]:hidden">
            {S.more}
            <span aria-hidden="true" className="text-slate-500 transition-transform group-open:rotate-180">&#9662;</span>
          </summary>
          <div className="space-y-3 px-3 pb-3">
            <p className="text-sm text-slate-600">{S.hint}</p>
            <ChipGroup label={S.budget} options={BUDGET_CHOICES} value={q.budget} onPick={pick('budget')} />
            <ChipGroup label={S.timeline} options={TIMELINE_CHOICES} value={q.timeline} onPick={pick('timeline')} />
            <ChipGroup label={S.financing} options={FINANCING_CHOICES} value={q.financing} onPick={pick('financing')} />
            <div>
              <label htmlFor={id + '-msg'} className="text-sm font-medium">{S.message}</label>
              <textarea id={id + '-msg'} name="message" rows={3} maxLength={1000} value={message} onChange={(e) => setMessage(e.target.value)}
                className={field + ' py-2'} />
            </div>
          </div>
        </details>
        {errors.form && <p role="alert" className="text-sm text-red-700">{errors.form}</p>}
        <button type="submit" disabled={busy}
          className="min-h-[52px] w-full rounded-xl bg-[var(--site-primary)] px-6 text-lg font-bold text-[var(--site-on-primary)] disabled:opacity-60">
          {busy ? 'Sending...' : submitLabel}
        </button>
      </form>
    </section>
  )
}
