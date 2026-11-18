'use client'
import React, { useEffect, useRef, useState } from 'react'
import { Btn, ErrorBox, LinkBtn, Spinner, inputCls } from '@/components/app/ui'
import { errorMessage } from '@/lib/app/client'
import { buildWhatsappUrl } from '@/lib/app/leads'
import { timeAgo } from '@/lib/app/format'
import { buyerMindApi, CAN_ANSWER_LABEL, TEMPERATURE_LABEL, type BriefView } from '@/lib/app/buyerMind'

/** The buyer mind's reading of this lead (docs/plan/buyer-mind.md): who they are, what to tell them, what to do next, and a
 * draft the agent edits and sends from their own WhatsApp. Nothing is sent from here. */
export function BuyerBrief({ leadId, phone }: { leadId: string; phone: string }) {
  const [view, setView] = useState<BriefView | null>(null)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const seq = useRef(0)

  function show(v: BriefView) {
    setView(v)
    setText(v.brief?.draft ?? '')
  }

  useEffect(() => {
    const mine = ++seq.current
    buyerMindApi.brief(leadId).then((v) => { if (mine === seq.current) show(v) }, (e) => { if (mine === seq.current) setError(errorMessage(e)) })
    return () => { seq.current++ }
  }, [leadId])

  async function think() {
    const mine = ++seq.current
    setBusy(true)
    setError(null)
    try {
      const v = await buyerMindApi.think(leadId)
      if (mine === seq.current) show(v)
    } catch (e) {
      if (mine === seq.current) setError(errorMessage(e))
    } finally {
      if (mine === seq.current) setBusy(false)
    }
  }

  const b = view?.brief
  return (
    <section aria-label="Buyer brief" className="space-y-3 rounded-2xl border border-indigo-200 bg-indigo-50/40 p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-semibold">Buyer brief</h2>
        {b && <span className="text-sm font-semibold text-gray-700">{TEMPERATURE_LABEL[b.temperature]}</span>}
      </div>
      {!view && !error && <Spinner label="Loading" />}
      {view && !b && !busy && <p className="text-sm text-gray-700">Not thought about yet. The assistant reads this lead, looks up the project and the area, and prepares what to say.</p>}
      {busy && <Spinner label="Thinking it through (up to a minute)" />}
      {error && <ErrorBox message={error} />}

      {b && !busy && (
        <div className="space-y-3 text-sm">
          {b.buyer && <p className="text-base font-semibold text-gray-900">{b.buyer}</p>}
          {b.flags.length > 0 && (
            <div role="note" aria-label="Tell them" className="rounded-xl border border-amber-300 bg-amber-50 p-3">
              <p className="font-semibold text-amber-900">Tell them</p>
              <ul className="list-disc pl-5 text-amber-900">{b.flags.map((f) => <li key={f}>{f}</li>)}</ul>
            </div>
          )}
          {b.asked_for && <p><span className="font-semibold">Asked for:</span> {b.asked_for} · {CAN_ANSWER_LABEL[b.can_answer]}</p>}
          {b.price_idea && <p><span className="font-semibold">Price idea:</span> {b.price_idea} <span className="text-gray-500">(indicative, not a quote)</span></p>}
          {b.implied.length > 0 && (
            <div>
              <p className="font-semibold">What it suggests</p>
              <ul className="list-disc pl-5 text-gray-800">{b.implied.map((x) => <li key={x}>{x}</li>)}</ul>
            </div>
          )}
          {b.unknown.length > 0 && <p><span className="font-semibold">Ask them:</span> {b.unknown.join(', ')}</p>}
          {b.alternatives.length > 0 && (
            <div>
              <p className="font-semibold">Also show them</p>
              <ul className="space-y-1">
                {b.alternatives.map((a) => (
                  <li key={a.slug}>
                    {/* a page of the public site: a plain link, never Next's Link (CLAUDE.md rule 10) */}
                    <a className="font-semibold text-indigo-800 underline" href={`/projects/${a.slug}`} target="_blank" rel="noopener noreferrer">{a.name || a.slug}</a>
                    {a.why && <span className="text-gray-700">: {a.why}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {b.next_step && <p className="rounded-xl bg-white p-3 font-semibold text-gray-900">Next: {b.next_step} ({b.when})</p>}

          {b.draft ? (
            <div className="space-y-2">
              <label className="block font-semibold" htmlFor="brief-draft">Suggested reply (edit before sending)</label>
              <textarea id="brief-draft" rows={6} className={`${inputCls} !min-h-[140px] py-3`} value={text} onChange={(e) => setText(e.target.value)} />
              <LinkBtn variant="whatsapp" href={buildWhatsappUrl(phone, text)} target="_blank" rel="noopener noreferrer">Send from my WhatsApp</LinkBtn>
              <p className="text-xs text-gray-500">Nothing is sent until you tap Send in WhatsApp.</p>
            </div>
          ) : (
            b.by === 'mind' && <p className="text-gray-700">No reply suggested: the checks left it out. Call them instead.</p>
          )}
          {b.why && <p className="text-gray-700"><span className="font-semibold">Why:</span> {b.why}</p>}
          <p className="text-xs text-gray-500">
            {b.by === 'rules' ? 'From the lead’s details only (the assistant could not think it through).' : `Confidence: ${b.confidence}.`}
            {view?.at ? ` Thought ${timeAgo(view.at)}.` : ''}
            {b.problems.length > 0 ? ` Left out by the checks: ${b.problems.join('; ')}.` : ''}
          </p>
        </div>
      )}
      <Btn variant="secondary" disabled={busy} onClick={think}>{b ? 'Think again' : 'Think about this lead'}</Btn>
    </section>
  )
}
