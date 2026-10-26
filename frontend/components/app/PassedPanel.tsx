'use client'
import Link from 'next/link'
import React from 'react'
import { Btn, ErrorBox, Spinner, inputCls } from '@/components/app/ui'
import { errorMessage } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { inboxApi, whatsappWent, type PassAgent, type PassedLead, type RouteRow } from '@/lib/app/inbox'

/** One rule row: "Wagholi -> House Deal, 3 passed", with Stop. */
function RuleRow({ r, onRemove }: { r: RouteRow; onRemove: () => void }) {
  return (
    <li className="flex items-center gap-2 rounded-xl bg-white p-3 text-sm">
      <span className="flex-1">
        <b>{r.label}</b> {r.kind === 'project' ? '(project)' : '(area)'} &rarr; {r.agent_name}
        <span className="text-gray-500"> · {r.passed} passed</span>
      </span>
      <Btn variant="ghost" block={false} onClick={onRemove}>Stop</Btn>
    </li>
  )
}

/** Owner: add a rule by hand (an area name; a project rule is made from a lead's pass box, which knows the page). */
function AddRule({ agents, onAdded }: { agents: PassAgent[]; onAdded: () => void }) {
  const [area, setArea] = React.useState('')
  const [agent, setAgent] = React.useState('')
  const [error, setError] = React.useState<string | null>(null)
  async function add() {
    setError(null)
    try {
      await inboxApi.addRoute(agent, 'area', area.trim())
      setArea('')
      onAdded()
    } catch (e) {
      setError(errorMessage(e))
    }
  }
  return (
    <div className="space-y-2 rounded-xl border border-gray-200 bg-white p-3">
      <p className="text-sm font-semibold">Pass every lead from an area to one agent</p>
      <input aria-label="Area" className={inputCls} placeholder="Area, e.g. Wagholi" value={area} onChange={(e) => setArea(e.target.value)} />
      <select aria-label="Agent" className={inputCls} value={agent} onChange={(e) => setAgent(e.target.value)}>
        <option value="">Pick an agent</option>
        {agents.map((a) => <option key={a.agent_id} value={a.agent_id}>{a.name}{a.slug ? ` (/agent/${a.slug})` : ''}</option>)}
      </select>
      {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
      <Btn disabled={!area.trim() || !agent} onClick={add}>Add rule</Btn>
    </div>
  )
}

function PassedRow({ p }: { p: PassedLead }) {
  const [open, setOpen] = React.useState(false)
  const went = whatsappWent(p.whatsapp_status)
  return (
    <li className="space-y-2 rounded-xl bg-white p-3 text-sm">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="block w-full text-left">
        <span className="font-semibold">{p.name || 'A buyer'}</span> &rarr; {p.agent_name}
        <span className="block text-xs text-gray-600">
          {timeAgo(p.passed_at)} · {p.by === 'auto' ? `by your ${p.rule ?? ''} rule` : 'by you'} ·{' '}
          {went ? 'WhatsApp to them sent' : p.whatsapp_status ? <span className="text-amber-800">WhatsApp to them not sent{p.whatsapp_error ? `: ${p.whatsapp_error}` : ''}</span> : 'no WhatsApp record'}
        </span>
      </button>
      {open && p.text && <p className="whitespace-pre-line break-words rounded-lg bg-gray-50 p-2 text-gray-900">{p.text}</p>}
      {open && <Link href={`/studio/leads/${encodeURIComponent(p.lead_id)}`} className="block text-blue-700 underline">Open the lead and its chats</Link>}
      {p.whatsapp_url && (open || !went) && (
        <a href={p.whatsapp_url} target="_blank" rel="noreferrer"
          className="flex min-h-[44px] items-center justify-center rounded-xl bg-green-600 px-4 font-semibold text-white">Send the details from my WhatsApp</a>
      )}
    </li>
  )
}

/** Leads > Passed (owner): the last 14 days' passes and the rules that pass leads by themselves. */
export function PassedPanel() {
  const [rows, setRows] = React.useState<PassedLead[] | null>(null)
  const [rules, setRules] = React.useState<RouteRow[]>([])
  const [agents, setAgents] = React.useState<PassAgent[]>([])
  const [error, setError] = React.useState<string | null>(null)
  const load = React.useCallback(() => {
    Promise.all([inboxApi.passed(), inboxApi.routes(), inboxApi.agents()])
      .then(([p, r, a]) => { setRows(p); setRules(r); setAgents(a) })
      .catch((e) => setError(errorMessage(e)))
  }, [])
  React.useEffect(load, [load])
  async function remove(id: string) {
    try {
      await inboxApi.removeRoute(id)
      load()
    } catch (e) {
      setError(errorMessage(e))
    }
  }
  if (error) return <ErrorBox message={error} onRetry={load} />
  if (!rows) return <Spinner />
  return (
    <div className="space-y-4">
      <section className="space-y-2">
        <h2 className="font-semibold">Passed by themselves</h2>
        {rules.length === 0
          ? <p className="text-sm text-gray-600">No rules yet. Pass a lead and pick "every lead from this area", or add one here.</p>
          : <ul className="space-y-2 p-0">{rules.map((r) => <RuleRow key={r.id} r={r} onRemove={() => remove(r.id)} />)}</ul>}
        <AddRule agents={agents} onAdded={load} />
      </section>
      <section className="space-y-2">
        <h2 className="font-semibold">Passed in the last 14 days</h2>
        {rows.length === 0
          ? <p className="text-sm text-gray-600">Nobody passed yet.</p>
          : <ul className="space-y-2 p-0">{rows.map((p) => <PassedRow key={p.lead_id} p={p} />)}</ul>}
      </section>
    </div>
  )
}
