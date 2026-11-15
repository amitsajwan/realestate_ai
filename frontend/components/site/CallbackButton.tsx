'use client'

import React, { useId, useState } from 'react'
import { BRAND_NAME } from '@/lib/brand'
import { normalizeIndianMobile } from '@/lib/site/phone'
import { contactName, contactNameStart } from '@/lib/site/strings'
import { submitInquiry } from '@/lib/site/tracking'

const HOUSE_AGENT = process.env.NEXT_PUBLIC_DEFAULT_AGENT_SLUG || 'avasetu'

/** The line a call-back lead carries (backend inbox/handover.ask_of reads "Call back: <topic>" as "A call back"). */
export function callbackMessage(topic: string): string {
  return `Call back: ${topic}`
}

type Props = {
  /** what the call is about: "<MahaRERA name> (MahaRERA <regno>)", as the page's enquiry form says it */
  topic: string
  agentSlug?: string
  agentName?: string
  /** "dark" on the project hero's dark band, "light" on a white card */
  tone?: 'dark' | 'light'
  label?: string
}

/** "Call me back": a number and a tick, nothing else (a portal's one-field call back, homebazaar.com 2026-11-15). The buyer ticks
 *  consent themselves (DPDP Act: never pre-ticked). It is a form lead like any other, with no name (backend InquiryIn.callback). */
export default function CallbackButton({ topic, agentSlug = HOUSE_AGENT, agentName = BRAND_NAME, tone = 'light', label = 'Call me back' }: Props) {
  const id = useId()
  const [open, setOpen] = useState(false)
  const [phone, setPhone] = useState('')
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const dark = tone === 'dark'
  const who = contactName(agentName)

  const send = async (e: React.FormEvent) => {
    e.preventDefault()
    const n = normalizeIndianMobile(phone)
    if (!n) return setError('Enter a valid 10-digit Indian mobile number (starts with 6-9)')
    if (!consent) return setError(`Please tick the box so ${who} can call you`)
    setError(null)
    setBusy(true)
    const ok = await submitInquiry(agentSlug, undefined, { name: '', phone: n, message: callbackMessage(topic), consent, callback: true })
    setBusy(false)
    if (ok) setDone(true)
    else setError('Could not send. Please try again or use WhatsApp.')
  }

  if (done) {
    return (
      <p role="status" className={`rounded-xl px-4 py-3 text-sm font-semibold ${dark ? 'bg-white/10 text-white' : 'bg-emerald-50 text-emerald-900'}`} data-testid="callback-done">
        Thank you. {contactNameStart(agentName)} will call you soon.
      </p>
    )
  }
  if (!open) {
    return (
      <button type="button" onClick={() => setOpen(true)} data-testid="callback-open"
        className={`inline-flex min-h-[44px] items-center gap-2 rounded-full px-5 text-sm font-semibold ${dark
          ? 'text-white ring-1 ring-inset ring-white/30 hover:bg-white/10' : 'border border-[#0f2340] text-[#0f2340]'}`}>
        <span aria-hidden>📞</span>{label}
      </button>
    )
  }
  return (
    <form onSubmit={send} noValidate className={`w-full max-w-sm rounded-xl p-3 ${dark ? 'bg-white text-slate-900' : 'border border-slate-200 bg-slate-50'}`} data-testid="callback-form">
      <label htmlFor={id + '-phone'} className="text-sm font-semibold text-slate-900">Your mobile number</label>
      <div className="mt-1 flex gap-2">
        <input id={id + '-phone'} type="tel" inputMode="tel" autoComplete="tel" placeholder="98765 43210" autoFocus value={phone}
          onChange={(e) => setPhone(e.target.value)} aria-invalid={!!error} aria-describedby={error ? id + '-err' : undefined}
          className="block min-h-[44px] w-full min-w-0 rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-900 placeholder:text-slate-400" />
        <button type="submit" disabled={busy} className="min-h-[44px] shrink-0 rounded-lg bg-amber-400 px-4 font-bold text-slate-900 disabled:opacity-60">
          {busy ? 'Sending...' : 'Call me'}
        </button>
      </div>
      <label className="mt-2 flex min-h-[44px] items-center gap-2">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="h-5 w-5 flex-none" />
        <span className="text-xs text-slate-700">I agree to be called by {who} about this.</span>
      </label>
      {error && <p id={id + '-err'} role="alert" className="text-sm text-red-700">{error}</p>}
    </form>
  )
}
