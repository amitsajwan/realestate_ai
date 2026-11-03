'use client'
import React from 'react'
import { Btn, Spinner, inputCls } from '@/components/app/ui'
import { errorMessage } from '@/lib/app/client'
import { inboxApi, whatsappWent, type Always, type Handover, type HandoverCard, type PassAgent, type PassResult } from '@/lib/app/inbox'

/** The handover card as the agent reads it: label and value per line, then what is still unknown. */
export function HandoverCardView({ card }: { card: HandoverCard }) {
  return (
    <div className="space-y-2 rounded-xl bg-gray-50 p-3 text-sm">
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
        {card.lines.map((l) => (
          <React.Fragment key={l.label}>
            <dt className="font-semibold text-gray-600">{l.label}</dt>
            <dd className="break-words text-gray-900">{l.value}</dd>
          </React.Fragment>
        ))}
      </dl>
      {card.missing.length > 0 && <p className="text-amber-800">Not known yet, they should ask: {card.missing.join(', ')}</p>}
    </div>
  )
}

/** After a pass: whether the card reached the agent on WhatsApp, and the owner's own-phone link as the fallback. */
export function PassedNote({ r }: { r: PassResult }) {
  const went = whatsappWent(r.whatsapp_status)
  return (
    <section aria-label="Passed" className="space-y-2 rounded-2xl border border-sky-200 bg-sky-50 p-3">
      <p className="text-sm font-semibold text-sky-900">Passed to {r.passed_to}. The lead and its chats are now in their Studio.</p>
      {went && <p className="text-sm text-sky-900">The full details went to {r.passed_to} on WhatsApp from our number.</p>}
      {!went && r.whatsapp_status && <p className="text-sm text-amber-800">The WhatsApp to them did not go out ({r.whatsapp_error || r.whatsapp_status}). Send it from your phone:</p>}
      {r.rule_added && <p className="text-sm text-sky-900">From now on, leads about {r.rule_added.label} go to {r.passed_to} by themselves.</p>}
      {r.whatsapp_url ? (
        <a href={r.whatsapp_url} target="_blank" rel="noreferrer"
          className={`flex min-h-[48px] items-center justify-center rounded-xl px-4 font-semibold ${went ? 'border border-green-600 text-green-700' : 'bg-green-600 text-white'}`}>
          {went ? 'Also send from my WhatsApp' : `Send the details to ${r.passed_to} on WhatsApp`}
        </a>
      ) : (
        <p className="text-sm text-gray-700">Their site has no mobile number, so call them with the buyer's details.</p>
      )}
    </section>
  )
}

/**
 * Owner only: pass this buyer to an agent, from the lead page (leadId) or a chat (threadId; a chat with a lead passes the whole
 * lead). The owner sees the card the agent will get first, and can make the pass a rule for the lead's area or project.
 */
export function PassBox({ leadId, threadId, onPassed }: { leadId?: string | null; threadId?: string; onPassed?: (r: PassResult) => void }) {
  const [open, setOpen] = React.useState(false)
  const [agents, setAgents] = React.useState<PassAgent[] | null>(null)
  const [info, setInfo] = React.useState<Handover | null>(null)
  const [pick, setPick] = React.useState('')
  const [always, setAlways] = React.useState<Always>(null)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [done, setDone] = React.useState<PassResult | null>(null)

  React.useEffect(() => {
    if (!open) return
    if (!agents) inboxApi.agents().then(setAgents).catch((e) => setError(errorMessage(e)))
    if (leadId && !info) {
      inboxApi.handover(leadId).then((h) => {
        setInfo(h)
        if (h.rule) setPick((p) => p || h.rule!.agent_id)
      }).catch(() => undefined)   // the card is a preview: passing works without it
    }
  }, [open, agents, info, leadId])

  async function pass() {
    setBusy(true)
    setError(null)
    try {
      const r = leadId ? await inboxApi.passLead(leadId, pick, always) : await inboxApi.pass(threadId!, pick, always)
      setDone(r)
      onPassed?.(r)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (done) return <PassedNote r={done} />
  if (!open) return <Btn variant="secondary" onClick={() => setOpen(true)}>Pass to an agent</Btn>
  const area = info?.areas[0]
  return (
    <section aria-label="Pass to an agent" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-3">
      {info && (
        <div className="space-y-1">
          <p className="text-sm font-semibold text-gray-800">What the agent gets</p>
          <HandoverCardView card={info.card} />
        </div>
      )}
      <label htmlFor="pass-agent" className="block text-sm font-semibold text-gray-800">Pass this buyer to</label>
      {!agents && !error ? <Spinner /> : (
        <select id="pass-agent" className={inputCls} value={pick} onChange={(e) => setPick(e.target.value)}>
          <option value="">Pick an agent</option>
          {(agents ?? []).map((a) => <option key={a.agent_id} value={a.agent_id}>{a.name}{a.slug ? ` (/agent/${a.slug})` : ''}{a.has_whatsapp ? '' : ' (no mobile on site)'}</option>)}
        </select>
      )}
      {info?.rule && <p className="text-xs text-gray-600">Your {info.rule.label} rule picks this agent.</p>}
      {(area || info?.project) && !info?.rule && (
        <fieldset className="space-y-1 text-sm text-gray-800">
          <legend className="font-semibold">Next time</legend>
          <label className="flex min-h-[40px] items-center gap-2"><input type="radio" name="always" checked={always === null} onChange={() => setAlways(null)} /> Ask me again</label>
          {area && <label className="flex min-h-[40px] items-center gap-2"><input type="radio" name="always" checked={always === 'area'} onChange={() => setAlways('area')} /> Pass every {area} lead to this agent by itself</label>}
          {info?.project && <label className="flex min-h-[40px] items-center gap-2"><input type="radio" name="always" checked={always === 'project'} onChange={() => setAlways('project')} /> Pass every {info.project.name} lead to this agent by itself</label>}
        </fieldset>
      )}
      {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
      <Btn disabled={busy || !pick} onClick={pass}>{busy ? 'Passing...' : 'Pass'}</Btn>
      <p className="text-xs text-gray-500">The lead and its chats move to the agent. They get these details in Studio and on WhatsApp from our number.</p>
    </section>
  )
}
