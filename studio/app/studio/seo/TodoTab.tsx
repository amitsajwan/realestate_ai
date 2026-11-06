'use client'
import React, { useState } from 'react'
import { LinkOut, StatusPill } from '@/components/app/list'
import type { PillTone } from '@/components/app/list'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { errorMessage } from '@/lib/app/client'
import { decideSplit, getRankings } from '@/lib/app/insights'
import type { CompetingKind, CompetingSearch, SplitDecided, SplitProject, SplitView } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'

// SEO → To do: what asks for the owner, each list saying what it means and what to do (backend seo/splits.py). The numbers stay on Rankings.
const SITE = process.env.NEXT_PUBLIC_SITE_URL || 'https://avasetu.in'
const card = 'list-none rounded-2xl bg-white p-3'
const btn = 'min-h-[44px] rounded-xl border border-gray-300 px-3 text-sm font-semibold text-[#0f2340] active:bg-gray-100 disabled:text-gray-400'
const primary = 'min-h-[44px] rounded-xl bg-[#0f2340] px-3 text-sm font-semibold text-white disabled:opacity-60'
const seen = (n: number) => `seen ${n.toLocaleString('en-IN')} ${n === 1 ? 'time' : 'times'}`
const place = (p: number | null) => (p == null ? '' : ` · average place ${Math.round(p * 10) / 10}`)

const STATE: Record<SplitProject['state'], { label: string; tone: PillTone }> = {
  proved: { label: 'Proved, merges by itself', tone: 'ok' },
  waiting: { label: 'Web check running', tone: 'info' },
  no_proof: { label: 'Needs your call', tone: 'action' },
}

/** Worth a decision today: buyers already see its pages, or it is in our areas. The others wait behind "Show all". */
const worthDeciding = (r: SplitProject) => r.state !== 'proved' && (r.searches.length > 0 || r.impressions > 0 || r.ours)

function SplitRow({ r, onDone }: { r: SplitProject; onDone: () => void }) {
  const [asking, setAsking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const regnos = r.members.map((m) => m.regno)
  const act = async (decision: 'same' | 'apart') => {
    setBusy(true); setErr(null)
    try { await decideSplit(regnos, decision); onDone() } catch (e) { setErr(errorMessage(e)); setBusy(false) }
  }
  return (
    <li className={card}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900">{r.name}</p>
          <p className="text-xs text-gray-600">{r.where}{r.homes ? ` · ${r.homes.toLocaleString('en-IN')} homes` : ''} · {r.members.length} pages</p>
        </div>
        <StatusPill tone={STATE[r.state].tone}>{STATE[r.state].label}</StatusPill>
      </div>
      {r.searches.map((s) => (
        <p key={s.phrase} className="mt-1 text-sm text-gray-800">Buyers searched &quot;{s.phrase}&quot; and Google showed these pages: {seen(s.impressions)}{place(s.position)}.</p>
      ))}
      {r.hint && <p className="mt-1 text-sm text-amber-900">{r.hint}</p>}
      <ul className="mt-1 space-y-0.5 p-0">
        {r.members.map((m) => (
          <li key={m.regno} className="list-none break-words text-xs text-gray-700">
            {m.slug ? <LinkOut href={`${SITE}/projects/${m.slug}`}>{m.name}</LinkOut> : m.name}
            <span className="text-gray-500"> · {m.regno} · {m.in_search ? 'in search' : 'not in search'}{m.impressions ? ` · ${seen(m.impressions)}` : ''}</span>
          </li>
        ))}
      </ul>
      {asking ? (
        <div className="mt-2 rounded-xl bg-gray-50 p-2">
          <p className="text-sm text-gray-800">Put these {r.members.length} pages on one? The others will redirect to it. You can undo this below.</p>
          <div className="mt-1 flex flex-wrap gap-2">
            <button type="button" className={primary} disabled={busy} onClick={() => act('same')}>{busy ? 'Merging…' : 'Yes, merge'}</button>
            <button type="button" className={btn} disabled={busy} onClick={() => setAsking(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          {r.state !== 'proved' && <button type="button" className={btn} disabled={busy} onClick={() => setAsking(true)}>Same project</button>}
          <button type="button" className={btn} disabled={busy} onClick={() => act('apart')}>Keep separate</button>
        </div>
      )}
      {err && <p className="mt-1 text-sm text-red-700">{err}</p>}
    </li>
  )
}

function DecidedRow({ d, onDone }: { d: SplitDecided; onDone: () => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const undo = async () => {
    setBusy(true); setErr(null)
    try { await decideSplit(d.regnos, 'undo'); onDone() } catch (e) { setErr(errorMessage(e)); setBusy(false) }
  }
  return (
    <li className="flex list-none flex-wrap items-center justify-between gap-2 text-sm text-gray-800">
      <span>{d.name}: {d.decision === 'same' ? `merged, ${d.regnos.length} registrations on one page` : 'kept separate'}</span>
      <button type="button" className={btn} disabled={busy} onClick={undo}>Undo</button>
      {err && <span className="w-full text-sm text-red-700">{err}</span>}
    </li>
  )
}

function SplitSection({ s, onDone }: { s: SplitView; onDone: () => void }) {
  const [all, setAll] = useState(false)
  const worth = s.items.filter(worthDeciding)
  const shown = all ? s.items : worth
  return (
    <>
      <div className={card} data-testid="split-projects">
        <p className="font-semibold text-gray-900">One project on several pages</p>
        <p className="mt-1 text-sm text-gray-800">
          Builders register towers separately, so one project can get several pages here. Buyers search one name, and Google splits its trust
          across those pages. Merging puts them on one stronger page, and the old addresses redirect to it.
        </p>
        <p className="mt-1 text-sm text-gray-800">
          <span className="font-semibold">How to decide:</span> open the pages. Say Same project if they are one site sold under one name.
          Say Keep separate if each is sold on its own, like a township&apos;s sectors.
        </p>
        <dl className="mt-2 grid grid-cols-3 gap-2">
          <div><dt className="text-xs text-gray-600">Proved by the web</dt><dd className="text-lg font-semibold text-gray-900">{s.proved}</dd></div>
          <div><dt className="text-xs text-gray-600">Web check running</dt><dd className="text-lg font-semibold text-gray-900">{s.waiting}</dd></div>
          <div><dt className="text-xs text-gray-600">Needs your call</dt><dd className="text-lg font-semibold text-gray-900">{s.no_proof}</dd></div>
        </dl>
        <p className="mt-1 text-xs text-gray-600">
          Each day Google is asked for 4 of their MahaRERA numbers. When a page prints two numbers of one project, the pages merge by themselves, with no button.
          You only need to step in where buyers already see these pages.
        </p>
      </div>
      {shown.length === 0 ? <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">Nothing needs you here today.</p> : (
        <ul className="space-y-2 p-0">{shown.map((r) => <SplitRow key={r.members.map((m) => m.regno).join()} r={r} onDone={onDone} />)}</ul>
      )}
      {s.total > worth.length && (
        <button type="button" className={btn} onClick={() => setAll(!all)}>{all ? `Show the ${worth.length} worth deciding` : `Show all ${s.total}`}</button>
      )}
      {s.decided.length > 0 && (
        <div className={card}>
          <p className="font-semibold text-gray-900">Your decisions</p>
          <ul className="mt-1 space-y-1 p-0">{s.decided.map((d) => <DecidedRow key={d.regnos.join()} d={d} onDone={onDone} />)}</ul>
        </div>
      )}
    </>
  )
}

const COMPETING: { kind: CompetingKind; title: string; meaning: string }[] = [
  { kind: 'project_and_list', title: 'A project page and a list page', meaning: 'Normal: someone searched a project, and Google tried both its page and the area or builder list that names it. As the project page gets stronger, Google settles on it.' },
  { kind: 'lists', title: 'Two list or guide pages', meaning: 'Normal: both pages are about the same area. They only matter if the area searches stop rising.' },
  { kind: 'different', title: 'Different projects', meaning: 'Normal: the search words fit two separate projects. Merging them would be wrong.' },
]
const PAGE_KIND: Record<string, string> = { project: 'Project', area: 'Area list', builder: 'Builder', other: 'Page' }

function Competing({ items, total, at }: { items: CompetingSearch[]; total: number; at: string | null }) {
  return (
    <div className={card} data-testid="competing">
      <p className="font-semibold text-gray-900">Searches that show two of our pages ({total})</p>
      <p className="mt-1 text-sm text-gray-800">
        <span className="font-semibold">Nothing to do here.</span> Searches where two pages were really one project are already in the list above.
        {at ? ` Read ${timeAgo(at)}.` : ''}
      </p>
      {COMPETING.map(({ kind, title, meaning }) => {
        const rows = items.filter((c) => c.kind === kind)
        if (!rows.length) return null
        return (
          <details key={kind} className="mt-2 border-t border-gray-100 pt-2">
            <summary className="min-h-[44px] cursor-pointer text-sm font-semibold text-gray-900">{title} ({rows.length})</summary>
            <p className="text-sm text-gray-700">{meaning}</p>
            <ul className="mt-1 space-y-2 p-0">
              {rows.map((c) => (
                <li key={c.phrase} className="list-none text-xs text-gray-700">
                  <span className="font-medium text-gray-900">&quot;{c.phrase}&quot;</span> · {seen(c.impressions)}{place(c.position)}
                  <ul className="p-0 pl-3">
                    {c.pages.map((p) => <li key={p.path} className="list-none break-words">{PAGE_KIND[p.kind]}: <LinkOut href={SITE + p.path}>{p.label}</LinkOut></li>)}
                  </ul>
                </li>
              ))}
            </ul>
          </details>
        )
      })}
    </div>
  )
}

/** Search Console allows "Request indexing" only by hand: the pages most worth the owner's ~10 a day (seo/note.py). */
function AskGoogle({ pages }: { pages: { url: string; state: string | null; why: string }[] }) {
  const [all, setAll] = useState(false)
  return (
    <div className={card}>
      <p className="font-semibold text-gray-900">Ask Google to index: the next {pages.length} pages</p>
      <p className="mt-1 text-sm text-gray-800">Google has not taken these yet, and a request brings it sooner. 10 a day: Search Console → URL inspection → paste the address → Request indexing. List and guide pages first, they link many pages.</p>
      <ul className="mt-1 space-y-1 p-0">
        {(all ? pages : pages.slice(0, 10)).map((p) => (
          <li key={p.url} className="break-words text-xs text-gray-700"><LinkOut href={p.url}>{p.url.replace(SITE, '')}</LinkOut> · {p.why}</li>
        ))}
      </ul>
      {pages.length > 10 && <button type="button" className={`${btn} mt-2`} onClick={() => setAll(!all)}>{all ? 'Show 10' : `Show all ${pages.length}`}</button>}
    </div>
  )
}

export default function TodoTab() {
  const q = useAsync(() => getRankings(), [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = q.data!
  return (
    <>
      {d.split && <SplitSection s={d.split} onDone={q.reload} />}
      {!!d.request_indexing?.length && <AskGoogle pages={d.request_indexing} />}
      <Competing items={d.conflicts.items} total={d.conflicts.items.length} at={d.conflicts.at} />
    </>
  )
}
