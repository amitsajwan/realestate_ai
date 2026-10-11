'use client'

import React, { useEffect, useRef, useState } from 'react'
import { anonId, apiPath } from '@/lib/interest/api'
import { BHK_CHOICES, BUDGET_CHOICES, type BudgetKey } from '@/lib/site/qualification'

export type Step = 'start' | 'tapped' | 'saved'
/** After the one-tap: what the visitor is looking for, one question per screen, then the optional details form. */
export type Question = 'bhk' | 'budget' | 'details'
const QUESTIONS: Question[] = ['bhk', 'budget', 'details']
const nextOf = (q: Question): Question => QUESTIONS[Math.min(QUESTIONS.indexOf(q) + 1, QUESTIONS.length - 1)]

export const bhkLabel = (label: string) => `${label} BHK`

const ERRORS: Record<string, string> = {
  consent: 'Please tick the box so we can keep your details.',
  phone: 'Please enter a valid 10-digit Indian mobile number.',
  limit: 'That was a few too many tries. Please try again in a while.',
  down: 'We could not reach the server. Please try again in a moment.',
  gone: 'This link is no longer available.',
}

const NAVY = '#0f2340'
const field = 'mt-1 block min-h-[48px] w-full rounded-xl border border-[#cdbf99] bg-white px-3 text-base text-[#0f2340] focus:outline-none focus:ring-2 focus:ring-[#f0b440]'

/**
 * The one-tap button and the optional details form. Both are real HTML forms posting to /i/<code>/tap, so the base action
 * works without JavaScript; with JavaScript they use fetch and update in place.
 */
export default function InterestActions({ code, agentName, sample, consentWording, initialStep = 'start', initialError = '',
  initialQuestion = 'bhk', secondary = false }: {
  code: string; agentName: string; sample: boolean; consentWording: string; initialStep?: Step; initialError?: string
  initialQuestion?: Question
  /** WhatsApp is the main action above this, so the one-tap button is the outlined second choice. */
  secondary?: boolean
}) {
  const [step, setStep] = useState<Step>(initialStep)
  const [question, setQuestion] = useState<Question>(initialQuestion)
  const [bhk, setBhk] = useState<number | null>(null)
  const [budget, setBudget] = useState<BudgetKey | null>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const moved = useRef(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(ERRORS[initialError] || '')
  const [consent, setConsent] = useState(false)
  const clicked = useRef(false)

  useEffect(() => {
    if (clicked.current || step !== 'start') return
    clicked.current = true
    fetch(apiPath(code, '/click'), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ anon_id: anonId() }),
    }).catch(() => undefined)
  }, [code, step])

  useEffect(() => {
    if (moved.current) heading.current?.focus()  // after advancing, not on first render
  }, [question, step])

  const answers = () => {
    const b = BUDGET_CHOICES.find((c) => c.value === budget)
    return { ...(bhk != null ? { bhk } : {}), ...(b ? { budget_min_inr: b.min, budget_max_inr: b.max } : {}) }
  }

  /** One chip tap saves the answer on the lead and moves on. The answer is a nice-to-have: a failure still moves on. */
  function answer(e: React.FormEvent, q: 'bhk' | 'budget', value: number | BudgetKey) {
    e.preventDefault()
    const b = q === 'budget' ? BUDGET_CHOICES.find((c) => c.value === value) : undefined
    const body = q === 'bhk' ? { bhk: value } : { budget_min_inr: b?.min, budget_max_inr: b?.max }
    if (q === 'bhk') setBhk(value as number)
    else setBudget(value as BudgetKey)
    fetch(apiPath(code, '/answers'), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...body, anon_id: anonId() }),
    }).catch(() => undefined)
    moved.current = true
    setQuestion(nextOf(q))
  }

  function skip(e: React.MouseEvent) {
    e.preventDefault()
    moved.current = true
    setQuestion(nextOf(question))
  }

  async function send(body: Record<string, unknown>, next: Step, e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await fetch(apiPath(code), {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...body, anon_id: anonId() }),
      })
      if (res.ok) { moved.current = true; setStep(next) }
      else if (res.status === 429) setError(ERRORS.limit)
      else if (res.status === 422) setError(ERRORS.phone)
      else if (res.status === 400) setError(ERRORS.consent)
      else setError(ERRORS.down)
    } catch {
      setError(ERRORS.down)
    } finally {
      setBusy(false)
    }
  }

  const honeypot = (
    <div aria-hidden="true" style={{ position: 'absolute', left: '-9999px', height: 0, overflow: 'hidden' }}>
      <label>Leave this empty<input type="text" name="website" tabIndex={-1} autoComplete="off" defaultValue="" /></label>
    </div>
  )

  if (step === 'start') {
    return (
      <form method="post" action={`/i/${code}/tap`} onSubmit={(e) => send({}, 'tapped', e)} className="relative">
        {honeypot}
        <button type="submit" disabled={busy}
          className={secondary
            ? 'flex min-h-[52px] w-full items-center justify-center rounded-2xl border-2 border-[#0f2340] bg-white px-6 text-lg font-bold active:translate-y-px disabled:opacity-70'
            : 'flex min-h-[64px] w-full items-center justify-center rounded-2xl bg-[#f0b440] px-6 text-xl font-bold shadow-md active:translate-y-px disabled:opacity-70'}
          style={{ color: NAVY }}>
          {busy ? 'One moment...' : 'I am interested'}
        </button>
        <p className="mt-3 text-center text-sm text-slate-600">One tap. No form, no phone number needed.</p>
        {error && <p role="alert" className="mt-2 text-center text-sm font-medium text-red-700">{error}</p>}
      </form>
    )
  }

  return (
    <div>
      <div role="status" className="rounded-2xl border border-[#ead9ae] bg-[#fbf6ea] p-4" style={{ color: NAVY }}>
        <p className="text-lg font-bold">{step === 'saved' ? 'Thank you, your details are saved.' : 'Thank you, we have noted your interest.'}</p>
        <p className="mt-1 text-[15px] leading-relaxed text-slate-700">
          {step === 'saved'
            ? (sample ? `${agentName} will get in touch about similar real homes as they are listed.` : `${agentName} will contact you about this soon.`)
            : (sample
              ? 'This is a sample home, so it is not for sale. Your tap tells us what buyers like, and it helps us bring you real homes like it.'
              : `${agentName} can see that someone liked this. A couple of quick taps below help them reply with the right homes.`)}
        </p>
      </div>
      {error && step === 'tapped' && <p role="alert" className="mt-3 text-sm font-medium text-red-700">{error}</p>}
      {step === 'tapped' && question !== 'details' && (
        <QuestionStep key={question} code={code} question={question} heading={heading} onAnswer={answer} onSkip={skip} />
      )}
      {step === 'tapped' && question === 'details' && (
        <form method="post" action={`/i/${code}/tap`} className="relative mt-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
          onSubmit={(e) => {
            const f = new FormData(e.currentTarget)
            const phone = String(f.get('phone') || '').trim()
            const has = phone || String(f.get('name') || '').trim() || String(f.get('note') || '').trim()
            if (has && !consent) { e.preventDefault(); setError(ERRORS.consent); return }
            send({ name: f.get('name'), phone: f.get('phone'), note: f.get('note'), consent, website: f.get('website'), ...answers() }, 'saved', e)
          }}>
          {honeypot}
          <input type="hidden" name="step" value="details" />
          <p className="text-sm font-semibold text-slate-600">Step 3 of 3</p>
          <h2 ref={heading} tabIndex={-1} className="text-base font-bold outline-none" style={{ color: NAVY }}>Want a reply? <span className="font-normal text-slate-600">(optional)</span></h2>
          {summary(bhk, budget) && <p className="mt-1 text-sm font-semibold" style={{ color: NAVY }}>{summary(bhk, budget)}</p>}
          <p className="mt-1 text-sm text-slate-600">Only add what you are comfortable sharing. You can skip all of it.</p>
          <label className="mt-3 block text-sm font-semibold" htmlFor="i-name">Your name
            <input id="i-name" name="name" type="text" autoComplete="name" maxLength={100} className={field} />
          </label>
          <label className="mt-3 block text-sm font-semibold" htmlFor="i-phone">Mobile number
            <input id="i-phone" name="phone" type="tel" inputMode="tel" autoComplete="tel" maxLength={20} className={field} />
          </label>
          <label className="mt-3 block text-sm font-semibold" htmlFor="i-note">A question? <span className="font-normal text-slate-500">(optional)</span>
            <textarea id="i-note" name="note" rows={2} maxLength={500} className={field + ' py-2'} />
          </label>
          <label className="mt-3 flex min-h-[44px] items-start gap-3 text-sm">
            <input type="checkbox" name="consent" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1 h-6 w-6 flex-none" />
            <span>{consentWording}</span>
          </label>
          <button type="submit" disabled={busy}
            className="mt-3 flex min-h-[52px] w-full items-center justify-center rounded-xl bg-[#0f2340] px-4 text-base font-bold text-white disabled:opacity-70">
            {busy ? 'Sending...' : 'Send my details'}
          </button>
        </form>
      )}
    </div>
  )
}

function summary(bhk: number | null, budget: BudgetKey | null): string {
  const b = BHK_CHOICES.find((c) => c.value === bhk)
  const m = BUDGET_CHOICES.find((c) => c.value === budget)
  return [b ? bhkLabel(b.label) : '', m ? m.label : ''].filter(Boolean).join(' · ')
}

const STEPS = {
  bhk: { n: 1, title: 'Which configuration?', options: BHK_CHOICES.map((c) => ({ value: String(c.value), label: bhkLabel(c.label) })) },
  budget: { n: 2, title: 'Your budget?', options: BUDGET_CHOICES.map((c) => ({ value: c.value as string, label: c.label })) },
}

/**
 * One question: each chip is a submit button of a real form posting to /i/<code>/tap (no-JS path), so one tap saves and moves on.
 * With JavaScript the answer is sent with fetch and the next question shows in place.
 */
function QuestionStep({ code, question, heading, onAnswer, onSkip }: {
  code: string; question: 'bhk' | 'budget'; heading: React.RefObject<HTMLHeadingElement | null>
  onAnswer: (e: React.FormEvent, q: 'bhk' | 'budget', value: number | BudgetKey) => void
  onSkip: (e: React.MouseEvent) => void
}) {
  const s = STEPS[question]
  const id = `i-q-${question}`
  return (
    <form method="post" action={`/i/${code}/tap`} className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
      onSubmit={(e) => {
        const v = String(((e.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null)?.value || '')
        if (!v) { e.preventDefault(); return }
        onAnswer(e, question, question === 'bhk' ? Number(v) : (v as BudgetKey))
      }}>
      <input type="hidden" name="step" value={question} />
      <p className="text-sm font-semibold text-slate-600">Step {s.n} of 3</p>
      <div aria-hidden="true" className="mt-1 flex gap-1">
        {[1, 2, 3].map((i) => <span key={i} className={'h-1 flex-1 rounded-full ' + (i <= s.n ? 'bg-[#f0b440]' : 'bg-slate-200')} />)}
      </div>
      <h2 id={id} ref={heading} tabIndex={-1} className="mt-3 text-lg font-bold outline-none" style={{ color: NAVY }}>{s.title}</h2>
      <div role="group" aria-labelledby={id} className="mt-3 flex flex-wrap gap-2">
        {s.options.map((o) => (
          <button key={o.value} type="submit" name={question} value={o.value}
            className="min-h-[48px] min-w-[44px] rounded-full border border-slate-300 bg-white px-4 text-base font-medium text-slate-800 active:bg-[#0f2340] active:text-white">
            {o.label}
          </button>
        ))}
      </div>
      <a href={`/i/${code}?done=1&q=${nextOf(question)}`} onClick={onSkip}
        className="mt-2 inline-flex min-h-[44px] items-center text-sm font-semibold text-slate-600 underline underline-offset-2">
        Skip
      </a>
    </form>
  )
}
