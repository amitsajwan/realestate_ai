'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { submitInviteRequest, validateInvite, type InviteErrors } from '@/lib/marketing/invite'
import { INVITE, PATHS } from '@/lib/marketing/strings'

type Status = 'idle' | 'sending' | 'done'

/**
 * Short invite form: name, mobile and consent are the only things a phone user must fill.
 * City (default Pune) and a note live under "More details". `idPrefix` keeps ids unique if it appears twice on a page.
 */
export default function RequestInviteForm({ idPrefix = 'ri' }: { idPrefix?: string }) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [city, setCity] = useState('Pune')
  const [message, setMessage] = useState('')
  const [consent, setConsent] = useState(false)
  const [website, setWebsite] = useState('') // honeypot
  const [errors, setErrors] = useState<InviteErrors>({})
  const [formError, setFormError] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [donePhone, setDonePhone] = useState('')
  const doneRef = useRef<HTMLHeadingElement>(null)
  const id = (s: string) => idPrefix + '-' + s

  useEffect(() => {
    if (status === 'done') doneRef.current?.focus()
  }, [status])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (status === 'sending') return
    const { errors: errs, phone: p } = validateInvite({ name, phone, city, message, consent })
    setErrors(errs)
    setFormError('')
    if (Object.keys(errs).length || !p) return
    setStatus('sending')
    const result = await submitInviteRequest({ name, phone: p, city, message, consent, website })
    if (result === 'ok') {
      setDonePhone('+91 ' + p.slice(0, 5) + ' ' + p.slice(5))
      setStatus('done')
      return
    }
    setStatus('idle')
    setFormError(result === 'rate_limited' ? INVITE.errors.tooMany : result === 'invalid' ? INVITE.errors.invalid : INVITE.errors.network)
  }

  if (status === 'done') {
    const first = name.trim().split(/\s+/)[0]
    return (
      <section aria-live="polite" className="rounded-2xl border border-emerald-300 bg-emerald-50 p-6 text-emerald-950">
        <h2 ref={doneRef} tabIndex={-1} className="text-2xl font-bold outline-none">{INVITE.success.title(first)}</h2>
        <p className="mt-2 text-lg">{INVITE.success.body(donePhone)}</p>
        <Link href={PATHS.home} className="mt-5 inline-flex min-h-[48px] items-center rounded-xl bg-[#0f2340] px-6 font-semibold text-white no-underline hover:bg-[#183a5d]">
          {INVITE.success.back}
        </Link>
      </section>
    )
  }

  const field = 'mt-1 block min-h-[48px] w-full rounded-lg border border-slate-400 bg-white px-3 text-base text-slate-900 focus:border-[#0f2340] focus:outline-none focus:ring-2 focus:ring-[#f0b440]'
  const L = INVITE.labels
  const moreOpen = !!(errors.city || errors.message)
  return (
    <form onSubmit={onSubmit} noValidate aria-busy={status === 'sending'} className="space-y-4">
      <div>
        <label htmlFor={id('name')} className="font-semibold">{L.name}</label>
        <input id={id('name')} name="name" autoComplete="name" enterKeyHint="next" value={name} onChange={(e) => setName(e.target.value)} maxLength={100}
          aria-invalid={!!errors.name} aria-describedby={errors.name ? id('name-err') : undefined} className={field} />
        {errors.name && <p id={id('name-err')} role="alert" className="mt-1 text-sm text-red-700">{errors.name}</p>}
      </div>
      <div>
        <label htmlFor={id('phone')} className="font-semibold">{L.phone}</label>
        <input id={id('phone')} name="phone" type="tel" inputMode="tel" autoComplete="tel" enterKeyHint="done" placeholder="98765 43210"
          value={phone} onChange={(e) => setPhone(e.target.value)}
          aria-invalid={!!errors.phone} aria-describedby={id('phone-hint') + (errors.phone ? ' ' + id('phone-err') : '')} className={field} />
        <p id={id('phone-hint')} className="mt-1 text-sm text-slate-600">{INVITE.hints.phone}</p>
        {errors.phone && <p id={id('phone-err')} role="alert" className="mt-1 text-sm text-red-700">{errors.phone}</p>}
      </div>

      <details open={moreOpen} className="rounded-lg border border-slate-200 px-3">
        <summary className="flex min-h-[44px] cursor-pointer items-center text-sm font-semibold text-[#0f2340]">{INVITE.more}</summary>
        <div className="space-y-4 pb-3">
          <div>
            <label htmlFor={id('city')} className="font-semibold">{L.city}</label>
            <input id={id('city')} name="city" autoComplete="address-level2" value={city} onChange={(e) => setCity(e.target.value)} maxLength={60}
              aria-invalid={!!errors.city} aria-describedby={errors.city ? id('city-err') : undefined} className={field} />
            {errors.city && <p id={id('city-err')} role="alert" className="mt-1 text-sm text-red-700">{errors.city}</p>}
          </div>
          <div>
            <label htmlFor={id('message')} className="font-semibold">{L.message} <span className="font-normal text-slate-600">{L.optional}</span></label>
            <textarea id={id('message')} name="message" rows={3} maxLength={500} value={message} onChange={(e) => setMessage(e.target.value)}
              aria-describedby={id('message-hint') + (errors.message ? ' ' + id('message-err') : '')} className={field + ' py-2'} />
            <p id={id('message-hint')} className="mt-1 text-sm text-slate-600">{INVITE.hints.message}</p>
            {errors.message && <p id={id('message-err')} role="alert" className="mt-1 text-sm text-red-700">{errors.message}</p>}
          </div>
        </div>
      </details>

      {/* Honeypot: hidden from people and assistive tech; bots that fill every field give themselves away. */}
      <div aria-hidden="true" style={{ position: 'absolute', left: '-10000px', top: 'auto', width: 1, height: 1, overflow: 'hidden' }}>
        <label htmlFor={id('website')}>Website</label>
        <input id={id('website')} name="website" type="text" tabIndex={-1} autoComplete="off" value={website} onChange={(e) => setWebsite(e.target.value)} />
      </div>

      <div>
        <label className="flex min-h-[44px] items-start gap-3">
          <input type="checkbox" name="consent" checked={consent} onChange={(e) => setConsent(e.target.checked)}
            aria-invalid={!!errors.consent} aria-describedby={errors.consent ? id('consent-err') : undefined} className="mt-1 h-6 w-6 flex-none accent-[#0f2340]" />
          <span>{L.consent}</span>
        </label>
        {errors.consent && <p id={id('consent-err')} role="alert" className="mt-1 text-sm text-red-700">{errors.consent}</p>}
      </div>

      {formError && <p role="alert" className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-red-800">{formError}</p>}

      <button type="submit" disabled={status === 'sending'}
        className="min-h-[52px] w-full rounded-xl bg-[#f0b440] px-6 text-lg font-extrabold text-[#0f2340] hover:bg-[#f5c75e] disabled:opacity-60">
        {status === 'sending' ? L.sending : L.submit}
      </button>
      <p className="text-sm text-slate-600">
        {INVITE.privacyNote} <Link href={PATHS.privacy} className="text-[#0f2340] underline">{INVITE.privacyLink}</Link>
      </p>
    </form>
  )
}
