'use client'

import React, { useEffect, useState } from 'react'
import { normalizeIndianMobile } from '@/lib/site/phone'
import { whatsappLink } from '@/lib/site/links'
import { submitInquiry } from '@/lib/site/tracking'
import type { ProfilePicture } from '@/lib/site/profile'
import { Credit, Picture } from '@/components/site/ProfilePictures'

/** Who a floor-plan request goes to: the same agent as the page's enquiry form. */
export interface PlansLead {
  agentSlug: string
  agentName: string
  agentPhone?: string | null
  /** what the request is about, e.g. "Godrej Ivara (MahaRERA PR...)" */
  topic: string
  waMessage: string
}

const KEY = 'avasetu-plans-open'

function opened(topic: string): boolean {
  try {
    return (JSON.parse(localStorage.getItem(KEY) || '[]') as string[]).includes(topic)
  } catch {
    return false
  }
}

function remember(topic: string) {
  try {
    const seen = JSON.parse(localStorage.getItem(KEY) || '[]') as string[]
    localStorage.setItem(KEY, JSON.stringify([...seen.filter((t) => t !== topic), topic].slice(-50)))
  } catch {
    /* private window: the plans stay open for this visit only */
  }
}

/** A plan drawn in lines, blurred behind the form when we have no plan of the project yet: it shows what the form gives. */
function Sketch() {
  return (
    <svg viewBox="0 0 320 200" aria-hidden className="h-full w-full text-slate-400">
      <g fill="none" stroke="currentColor" strokeWidth="3">
        <rect x="10" y="10" width="300" height="180" />
        <path d="M130 10v110M10 120h190M200 70v120M200 70h110M250 70v60M250 130h60M60 120v70" />
      </g>
    </svg>
  )
}

/** Floor plans behind a short form (owner 2026-10-22): name, mobile and consent make a lead for the page's agent ("Floor plans
 * of ..."), then the plans we keep are shown; without any, the agent sends them on WhatsApp. Opened once per browser. */
export default function FloorPlansLock({ plans, name, lead }: { plans: ProfilePicture[]; name: string; lead: PlansLead }) {
  const [open, setOpen] = useState(false)
  const [who, setWho] = useState('')
  const [phone, setPhone] = useState('')
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => setOpen(opened(lead.topic)), [lead.topic])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const n = normalizeIndianMobile(phone)
    if (who.trim().length < 2) return setError('Please enter your name')
    if (!n) return setError('Enter a valid 10-digit Indian mobile number (starts with 6-9)')
    if (!consent) return setError('Please tick the box so ' + lead.agentName + ' can send you the plans')
    setBusy(true)
    const ok = await submitInquiry(lead.agentSlug, undefined, {
      name: who.trim(), phone: n, consent, message: `Floor plans of ${lead.topic}`,
    })
    setBusy(false)
    if (!ok) return setError('Could not send. Please try again or use WhatsApp.')
    remember(lead.topic)
    setOpen(true)
  }

  const wa = whatsappLink(lead.agentPhone, `${lead.waMessage} Please send the floor plans.`)
  const field = 'mt-1 block min-h-[48px] w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-900'
  return (
    <section aria-labelledby="plans-title" data-testid="plans" id="floor-plans" className="scroll-mt-20">
      <h2 id="plans-title" className="text-xl font-bold">Floor plans of {name}</h2>
      {open ? (
        plans.length > 0 ? (
          <>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {plans.map((p) => (
                <figure key={p.url}>
                  <div className="aspect-[16/10] [&_img]:object-contain"><Picture pic={p} /></div>
                  <figcaption className="mt-1 text-sm text-slate-700">{p.alt}</figcaption>
                </figure>
              ))}
            </div>
            <Credit pics={plans} name={name} />
            <p className="mt-2 text-sm text-slate-700">{lead.agentName} will also send you the plans of the flat you choose.</p>
          </>
        ) : (
          <div aria-live="polite" className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="font-semibold text-emerald-900">Thank you. {lead.agentName} will send you the floor plans of {name} on WhatsApp.</p>
            {wa && (
              <a href={wa} target="_blank" rel="noopener noreferrer"
                className="mt-3 inline-flex min-h-[48px] items-center justify-center rounded-xl bg-[#25D366] px-6 font-bold text-[#053b1a] no-underline">
                Ask on WhatsApp now
              </a>
            )}
          </div>
        )
      ) : (
        <div className="relative mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white px-4 py-6">
          <div aria-hidden className="pointer-events-none absolute inset-0 grid select-none grid-cols-2 content-start gap-2 p-3 blur-md">
            {plans.length > 0
              // eslint-disable-next-line @next/next/no-img-element
              ? plans.slice(0, 6).map((p) => <img key={p.url} src={p.url} alt="" className="aspect-[16/10] w-full object-contain" />)
              : [0, 1, 2, 3, 4, 5].map((i) => <div key={i} className="aspect-[16/10]"><Sketch /></div>)}
          </div>
          <form onSubmit={onSubmit} noValidate
            className="relative mx-auto max-w-sm space-y-3 rounded-2xl bg-white/95 p-4 shadow-lg">
            <p className="font-semibold text-slate-900">
              {plans.length > 0 ? `See the ${plans.length} floor plan${plans.length > 1 ? 's' : ''}` : 'Get the floor plans'}
            </p>
            <label className="block text-sm font-medium">Your name
              <input name="name" autoComplete="name" value={who} onChange={(e) => setWho(e.target.value)} className={field} />
            </label>
            <label className="block text-sm font-medium">Mobile number
              <input name="phone" type="tel" inputMode="tel" autoComplete="tel" placeholder="98765 43210" value={phone}
                onChange={(e) => setPhone(e.target.value)} className={field} />
            </label>
            <label className="flex min-h-[44px] items-start gap-3">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1 h-6 w-6 flex-none" />
              <span className="text-sm">I agree to be contacted by {lead.agentName} about this project.</span>
            </label>
            {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
            <button type="submit" disabled={busy}
              className="min-h-[48px] w-full rounded-xl bg-[var(--site-primary,#0f2340)] px-4 font-bold text-[var(--site-on-primary,#fff)] disabled:opacity-60">
              {busy ? 'Sending...' : plans.length > 0 ? 'Show the floor plans' : 'Send me the floor plans'}
            </button>
          </form>
        </div>
      )}
    </section>
  )
}
