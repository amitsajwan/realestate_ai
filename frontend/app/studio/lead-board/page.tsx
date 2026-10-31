'use client'
import Link from 'next/link'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { PassedNote } from '@/components/app/PassBox'
import { Btn, ErrorBox, PageTitle, Spinner, TempChip, inputCls } from '@/components/app/ui'
import { errorMessage } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import type { PassResult } from '@/lib/app/inbox'
import { BOARD_PATH, activityLine, boardApi, boardTitle, shareText, type BoardCard, type OfferKind } from '@/lib/app/leadBoard'
import { useAsync } from '@/lib/app/useAsync'

/**
 * Lead board (owner, 2026-10-31): our open buyer leads without the buyer's name or number. An agent asks for the ones they can
 * serve, with an offer if they like; the owner gives each lead to one agent, and only then do the name and number reach them.
 * The owner sends this page's link to agents on WhatsApp; the page is live (owner: "a realtime page for leads, not a WhatsApp
 * message only"): it reads the board again every LIVE_MS while open, and marks leads that came in since the viewer last looked.
 */
const LIVE_MS = 30_000
const SEEN_KEY = 'lead_board_seen'

function readSeen(): number {
  try { return Number(window.localStorage.getItem(SEEN_KEY)) || 0 } catch { return 0 }
}

function writeSeen(at: number) {
  try { window.localStorage.setItem(SEEN_KEY, String(at)) } catch { /* private window: no New marks next time */ }
}

export default function LeadBoardPage() {
  const { data, error, loading, reload } = useAsync(() => boardApi.get(), [])
  const [area, setArea] = useState<string | null>(null)
  const [updated, setUpdated] = useState<Date | null>(null)
  const [, tick] = useState(0)
  const seen = useRef<number | null>(null)
  if (seen.current === null && typeof window !== 'undefined') seen.current = readSeen()

  useEffect(() => {
    if (data) setUpdated(new Date())
  }, [data])
  useEffect(() => {
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') reload()
      tick((n) => n + 1)
    }, LIVE_MS)
    const back = () => { if (document.visibilityState === 'visible') reload() }
    document.addEventListener('visibilitychange', back)
    writeSeen(Date.now())
    return () => { clearInterval(id); document.removeEventListener('visibilitychange', back) }
  }, [reload])
  const isNew = (c: BoardCard) => !!seen.current && Date.parse(c.created_at.endsWith('Z') ? c.created_at : `${c.created_at}Z`) > seen.current
  const areas = useMemo(() => Array.from(new Set((data?.items ?? []).flatMap((c) => c.areas))).sort(), [data])
  const items = (data?.items ?? []).filter((c) => !area || c.areas.includes(area))

  return (
    <div className="space-y-4">
      <PageTitle action={updated && <span className="flex items-center gap-1.5 text-xs font-semibold text-green-700"><span className="h-2 w-2 animate-pulse rounded-full bg-green-600" />Live · {timeAgo(updated.toISOString())}</span>}>Lead board</PageTitle>
      <p className="text-sm text-gray-700">
        Buyers who asked {data?.owner ? 'us' : 'Avasetu'} about a home in the last {data?.days ?? 30} days. Their name and number stay
        hidden: {data?.owner ? 'agents ask for a lead, you give it to one of them.' : 'ask for the ones you can serve, and when a lead is given to you it comes to your Leads with the full details.'}
      </p>
      {data?.owner && <ShareBox items={data.items} />}
      {areas.length > 1 && (
        <div className="-mx-1 flex flex-wrap gap-2" role="group" aria-label="Area">
          {[null, ...areas].map((a) => (
            <button key={a ?? 'all'} type="button" onClick={() => setArea(a)}
              className={`min-h-[40px] rounded-full border px-3 text-sm font-semibold ${area === a ? 'border-[#0f2340] bg-[#0f2340] text-white' : 'border-gray-300 bg-white text-gray-800'}`}>
              {a ?? 'All areas'}
            </button>
          ))}
        </div>
      )}
      {loading && !data && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}
      {data && items.length === 0 && <p className="rounded-2xl bg-gray-50 p-4 text-sm text-gray-700">No open leads right now. New ones come up here as buyers ask.</p>}
      <ul className="space-y-3">
        {items.map((c) => <BoardRow key={c.ref} card={c} owner={data!.owner} fresh={isNew(c)} onChange={reload} />)}
      </ul>
    </div>
  )
}

function ShareBox({ items }: { items: BoardCard[] }) {
  const [copied, setCopied] = useState(false)
  const url = typeof window !== 'undefined' ? `${window.location.origin}${BOARD_PATH}` : BOARD_PATH
  const text = shareText(items, url)
  async function copy() {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }
  return (
    <section aria-label="Send to agents" className="space-y-2 rounded-2xl border border-green-200 bg-green-50 p-3">
      <p className="text-sm font-semibold text-green-900">Send this board to agents</p>
      <p className="text-xs text-green-900">They sign in with their number, see the leads below without names or numbers, and ask.</p>
      <a href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noreferrer"
        className="flex min-h-[48px] items-center justify-center rounded-xl bg-green-600 px-4 font-semibold text-white">Share on WhatsApp</a>
      <Btn variant="secondary" onClick={copy}>{copied ? 'Link copied' : 'Copy link'}</Btn>
    </section>
  )
}

function Chip({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-800">{children}</span>
}

function BoardRow({ card: c, owner, fresh, onChange }: { card: BoardCard; owner: boolean; fresh: boolean; onChange: () => void }) {
  const facts = [c.bhk, c.budget, c.when && `Buying: ${c.when}`, c.paying, c.wants].filter(Boolean) as string[]
  return (
    <li className={`space-y-3 rounded-2xl border bg-white p-4 ${fresh ? 'border-green-500' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          {fresh && <p className="text-xs font-bold uppercase tracking-wide text-green-700">New</p>}
          <h2 className="break-words font-semibold text-gray-900">{boardTitle(c)}</h2>
          {c.project && c.areas.length > 0 && <p className="text-sm text-gray-600">{c.areas.join(', ')}</p>}
        </div>
        <TempChip temperature={c.temperature} />
      </div>
      {facts.length > 0 && <div className="flex flex-wrap gap-1.5">{facts.map((f) => <Chip key={f}>{f}</Chip>)}</div>}
      <p className={`rounded-lg px-2 py-1 text-xs font-semibold ${c.genuine === 'talked' ? 'bg-green-50 text-green-800' : 'bg-amber-50 text-amber-800'}`}>
        {c.genuine === 'talked' ? 'Spoke with us' : 'Left a number, not reached yet'}
      </p>
      <ul className="space-y-0.5 text-sm text-gray-700">
        {c.signals.map((s) => <li key={s}>✓ {s}</li>)}
      </ul>
      <Looked card={c} />
      {c.caution && <p className="rounded-lg bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">⚠ {c.caution}</p>}
      {c.with_agent && (
        <p className="text-xs font-semibold text-gray-600">
          {owner ? `With ${c.holder ?? 'an agent'} now: giving it moves it from them.` : 'Already shared with one agent.'}
        </p>
      )}
      <p className="text-xs text-gray-500">{c.age} · from {c.came_from} · active {timeAgo(c.last_active_at)}{c.asked ? ` · ${c.asked} agent${c.asked === 1 ? '' : 's'} asked` : ''}</p>
      {owner ? <OwnerAsks card={c} onChange={onChange} /> : <AskBox card={c} onChange={onChange} />}
    </li>
  )
}

/** What they looked at on the site: visits, reading time, device and city, then the pages in order with minutes read. */
function Looked({ card: c }: { card: BoardCard }) {
  const a = c.activity
  if (!a || (!a.pages.length && !a.visits)) return null
  const line = activityLine(a)
  return (
    <details className="rounded-xl bg-gray-50 p-3 text-sm" open={a.pages.length <= 4}>
      <summary className="cursor-pointer font-semibold text-gray-800">
        What they looked at{a.page_count ? ` (${a.page_count} page${a.page_count === 1 ? '' : 's'})` : ''}
      </summary>
      {line && <p className="mt-1 text-xs text-gray-600">{line}</p>}
      <ol className="mt-2 space-y-0.5 text-gray-800">
        {a.pages.map((p) => (
          <li key={p.label} className="flex justify-between gap-2">
            <span className="min-w-0 break-words">{p.label}</span>
            {p.minutes > 0 && <span className="shrink-0 text-xs text-gray-500">{p.minutes} min</span>}
          </li>
        ))}
      </ol>
      {a.more_pages > 0 && <p className="mt-1 text-xs text-gray-500">and {a.more_pages} more</p>}
    </details>
  )
}

function AskBox({ card: c, onChange }: { card: BoardCard; onChange: () => void }) {
  const [open, setOpen] = useState(false)
  const [kind, setKind] = useState<OfferKind>(c.mine?.offer_kind ?? 'none')
  const [value, setValue] = useState(c.mine?.offer_value ? String(c.mine.offer_value) : '')
  const [note, setNote] = useState(c.mine?.note ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(fn: () => Promise<unknown>) {
    setBusy(true)
    setError(null)
    try {
      await fn()
      setOpen(false)
      onChange()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return c.mine ? (
      <div className="space-y-2 rounded-xl bg-sky-50 p-3 text-sm text-sky-900">
        <p className="font-semibold">You asked {timeAgo(c.mine.at)}{c.mine.offer ? `: ${c.mine.offer}` : ''}</p>
        <p>We will tell you here and on WhatsApp if it is given to you.</p>
        <div className="flex gap-2">
          <Btn variant="secondary" onClick={() => setOpen(true)}>Change</Btn>
          <Btn variant="secondary" disabled={busy} onClick={() => run(() => boardApi.withdraw(c.ref))}>Take back</Btn>
        </div>
        {error && <p role="alert" className="font-semibold text-red-700">{error}</p>}
      </div>
    ) : <Btn onClick={() => setOpen(true)}>Ask for this lead</Btn>
  }
  const num = Number(value)
  const ok = kind === 'none' || (num > 0 && (kind === 'fee' || num <= 100))
  return (
    <section aria-label="Ask for this lead" className="space-y-3 rounded-xl border border-gray-200 p-3">
      <fieldset className="space-y-1 text-sm text-gray-800">
        <legend className="font-semibold">Your offer (only we see it)</legend>
        {([['none', 'No offer, just interested'], ['fee', 'A fee for the lead (₹)'], ['share', 'A share of my brokerage when it closes (%)']] as const).map(([k, label]) => (
          <label key={k} className="flex min-h-[40px] items-center gap-2">
            <input type="radio" name={`offer-${c.ref}`} checked={kind === k} onChange={() => setKind(k)} /> {label}
          </label>
        ))}
      </fieldset>
      {kind !== 'none' && (
        <input className={inputCls} inputMode="numeric" aria-label={kind === 'fee' ? 'Fee in rupees' : 'Share in percent'}
          placeholder={kind === 'fee' ? 'e.g. 2000' : 'e.g. 25'} value={value} onChange={(e) => setValue(e.target.value.replace(/[^\d.]/g, ''))} />
      )}
      <input className={inputCls} maxLength={200} placeholder="Why you (optional): e.g. I have 3 resale 2 BHKs there" value={note} onChange={(e) => setNote(e.target.value)} />
      {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
      <Btn disabled={busy || !ok} onClick={() => run(() => boardApi.ask(c.ref, kind, kind === 'none' ? null : num, note))}>{busy ? 'Sending...' : 'Send'}</Btn>
      <button type="button" className="min-h-[44px] w-full text-sm font-semibold text-gray-600" onClick={() => setOpen(false)}>Cancel</button>
    </section>
  )
}

function OwnerAsks({ card: c, onChange }: { card: BoardCard; onChange: () => void }) {
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState<PassResult | null>(null)

  async function remove() {
    if (!window.confirm('Take this lead off the board? Agents will no longer see it.')) return
    setBusy('remove')
    setError(null)
    try {
      await boardApi.remove(c.ref)
      onChange()
    } catch (e) {
      setError(errorMessage(e))
      setBusy(null)
    }
  }

  async function give(agentId: string) {
    setBusy(agentId)
    setError(null)
    try {
      setDone(await boardApi.give(c.ref, agentId))
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  if (done) {
    return (
      <div className="space-y-2">
        <PassedNote r={done} />
        <Btn variant="secondary" onClick={onChange}>Done</Btn>
      </div>
    )
  }
  return (
    <div className="space-y-2">
      {c.lead_id && <Link href={`/studio/leads/${c.lead_id}`} className="text-sm font-semibold text-blue-700 underline">Open the lead</Link>}
      {(c.asks ?? []).length === 0 ? <p className="text-sm text-gray-600">No agent has asked yet.</p> : (
        <ul className="space-y-2">
          {c.asks!.map((a) => (
            <li key={a.agent_id} className="space-y-2 rounded-xl bg-gray-50 p-3 text-sm">
              <p><b>{a.agent_name}</b> · {timeAgo(a.at)} · {a.offer ?? 'no offer'}</p>
              {a.note && <p className="text-gray-700">“{a.note}”</p>}
              <Btn disabled={!!busy} onClick={() => give(a.agent_id)}>{busy === a.agent_id ? 'Giving...' : `Give to ${a.agent_name}`}</Btn>
            </li>
          ))}
        </ul>
      )}
      {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
      <button type="button" disabled={!!busy} onClick={remove} className="min-h-[44px] w-full text-sm font-semibold text-red-700">
        {busy === 'remove' ? 'Removing...' : 'Remove from board (a test, or I keep it)'}
      </button>
    </div>
  )
}
