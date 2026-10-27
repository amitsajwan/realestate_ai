'use client'
import Link from 'next/link'
import React from 'react'
import { useIsOwner } from '@/components/app/agents/useIsOwner'
import { countWaitingPosts } from '@/components/app/AppShell'
import { ReraReminder, reraDue } from '@/components/app/ReraReminder'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { WeeklyCard } from '@/components/app/WeeklyCard'
import { assetUrl, brandingApi, type BrandingDoc } from '@/lib/app/branding'
import { api, errorMessage } from '@/lib/app/client'
import { contentApi } from '@/lib/app/content'
import { freshnessOf, needingConfirmation } from '@/lib/app/freshness'
import {
  CALL_LIST_MAX, INVITE_KIND, PASSED_KIND, SEO_KIND, TRIAL_KIND, callList, callListGreeting, greeting, markSiteShared, setupSteps, siteShared, todoRows,
  type CallItem, type SetupStep, type TodoRow,
} from '@/lib/app/home'
import { inboxApi } from '@/lib/app/inbox'
import { buildWhatsappUrl } from '@/lib/app/leads'
import { getSiteUrl } from '@/lib/app/session'
import { whatsappShareUrl } from '@/lib/app/share'
import { useAsync } from '@/lib/app/useAsync'
import { getNotifications } from '@/lib/app/whatsapp'
import type { BusinessToday, Lead, Listing, WeeklyReport } from '@/lib/app/types'

/** A source that fails is left out of the screen, never an error on it (the server's day summary aside). */
function soft<T>(load: () => Promise<T>, fallback: T): Promise<T> {
  return Promise.resolve().then(load).catch(() => fallback)
}

interface HomeData {
  today: BusinessToday | null
  todayError: string | null
  leads: Lead[]
  listings: Listing[]
  week: WeeklyReport | null
  brand: BrandingDoc | null
  calls: CallItem[]
  todo: TodoRow[]
}

async function loadHome(owner: boolean): Promise<HomeData> {
  let todayError: string | null = null
  const [today, leads, listings, week, threads, notes, posts, brand] = await Promise.all([
    Promise.resolve().then(() => api.getToday()).catch((e) => { todayError = errorMessage(e); return null }),
    soft(() => api.listLeads(), [] as Lead[]),
    soft(() => api.listListings(), [] as Listing[]),
    soft(() => api.getWeeklyReport(), null as WeeklyReport | null),
    soft(() => inboxApi.threads(), []),
    soft(() => getNotifications(true).then((n) => n.items), []),
    owner ? soft(() => contentApi.getUpcoming().then(countWaitingPosts), 0) : Promise.resolve(0),
    soft(() => brandingApi.load(), null as BrandingDoc | null),
  ])
  const kind = (k: string) => notes.filter((x) => x.kind === k).length
  const weekly = (k: string) => week?.todo.find((x) => x.kind === k)?.count ?? 0
  const need = needingConfirmation(listings)
  const todo = todoRows({
    inbox: threads.filter((t) => t.needs_you).length,
    passed: kind(PASSED_KIND),
    posts,
    invites: kind(INVITE_KIND),
    trials: kind(TRIAL_KIND),
    seo: kind(SEO_KIND),
    photos: weekly('photos'),
    freshness: Math.max(need.length, weekly('freshness')),
    hidden: need.filter((l) => freshnessOf(l) === 'hidden').length,
  }, today?.actions)
  return { today, todayError, leads, listings, week, brand, calls: callList(today, leads), todo }
}

// ---- pieces --------------------------------------------------------------------------------------------------------------
function Header({ brand }: { brand: BrandingDoc | null }) {
  const name = brand?.agent_name?.trim().split(/\s+/)[0]
  const pic = assetUrl(brand?.photo || brand?.branding_data?.logo || '')
  const day = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })
  return (
    <header className="items-center gap-3 [display:flex]">
      <div className="min-w-0 flex-1">
        <p className="text-sm text-gray-500">{day}</p>
        <h1 className="truncate text-2xl font-bold text-gray-900">{greeting()}{name ? `, ${name}` : ''}</h1>
      </div>
      <Link href="/studio/profile" aria-label="My brand and website"
        className="h-12 w-12 flex-none items-center justify-center overflow-hidden rounded-full border border-gray-200 bg-[#e7ebf2] text-lg font-bold text-[#0f2340] [display:flex]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {pic ? <img src={pic} alt="" className="h-full w-full object-cover" /> : (name?.[0]?.toUpperCase() ?? '•')}
      </Link>
    </header>
  )
}

function QuickActions({ siteUrl, onShared }: { siteUrl: string | null; onShared: () => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Link href="/studio/listings/new" data-testid="quick-add-listing"
        className="min-h-[52px] items-center justify-center gap-2 rounded-xl bg-[#0f2340] px-3 text-base font-semibold text-white active:opacity-90 [display:flex]">
        <span aria-hidden className="text-xl leading-none">+</span> Add listing
      </Link>
      {siteUrl ? (
        <a href={whatsappShareUrl(`Namaste! Visit my property website: ${siteUrl}`)} target="_blank" rel="noopener noreferrer" onClick={onShared}
          data-testid="quick-share-site"
          className="min-h-[52px] items-center justify-center rounded-xl border border-green-600 bg-white px-3 text-center text-base font-semibold leading-tight text-green-700 active:bg-green-50 [display:flex]">
          Share my website
        </a>
      ) : (
        <Link href="/studio/leads" className="min-h-[52px] items-center justify-center rounded-xl border border-gray-300 bg-white px-3 text-base font-semibold text-gray-800 [display:flex]">
          All leads
        </Link>
      )}
    </div>
  )
}

function SetupCard({ steps }: { steps: SetupStep[] }) {
  const done = steps.filter((s) => s.done).length
  if (done === steps.length) return null
  const next = steps.find((s) => !s.done)!
  return (
    <section aria-label="Get set up" className="space-y-3 rounded-2xl border border-[#0f2340]/15 bg-white p-4">
      <div className="items-center justify-between gap-2 [display:flex]">
        <h2 className="font-bold text-gray-900">Get set up</h2>
        <span className="text-sm font-semibold tabular-nums text-gray-600">{done} of {steps.length} done</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-100" aria-hidden>
        <div className="h-full rounded-full bg-[#f0b440]" style={{ width: `${(done / steps.length) * 100}%` }} />
      </div>
      <ol className="space-y-1">
        {steps.map((s) => (
          <li key={s.key}>
            <Link href={s.href} data-testid={`setup-${s.key}`} aria-label={`${s.title}${s.done ? ' (done)' : ''}`}
              className={`min-h-[52px] items-center gap-3 rounded-xl px-2 [display:flex] ${s === next ? 'bg-amber-50' : ''}`}>
              <span aria-hidden className={`h-7 w-7 flex-none items-center justify-center rounded-full text-sm font-bold [display:flex] ${
                s.done ? 'bg-green-600 text-white' : s === next ? 'bg-[#0f2340] text-white' : 'border-2 border-gray-300 text-gray-400'}`}>
                {s.done ? '✓' : steps.indexOf(s) + 1}
              </span>
              <span className="min-w-0 flex-1">
                <span className={`block font-semibold ${s.done ? 'text-gray-500 line-through' : 'text-gray-900'}`}>{s.title}</span>
                {s === next && <span className="block text-sm text-gray-600">{s.detail}</span>}
              </span>
              {!s.done && <span aria-hidden className="text-xl text-gray-400">›</span>}
            </Link>
          </li>
        ))}
      </ol>
    </section>
  )
}

const TONE_DOT: Record<CallItem['tone'], string> = {
  bad: 'bg-red-600', action: 'bg-[#f0b440]', hot: 'bg-orange-500', due: 'bg-blue-600',
}

function CallRow({ c, onCall }: { c: CallItem; onCall: (c: CallItem) => void }) {
  return (
    <li className="items-center gap-2 py-2 [display:flex]" data-testid="call-row">
      <Link href={`/studio/leads/${c.id}`} className="min-h-[48px] min-w-0 flex-1 items-center gap-3 [display:flex]">
        <span aria-hidden className={`h-2.5 w-2.5 flex-none rounded-full ${TONE_DOT[c.tone]}`} />
        <span className="min-w-0">
          <span className="block truncate font-semibold text-gray-900">{c.name}</span>
          <span className={`block truncate text-sm ${c.tone === 'bad' ? 'text-red-700' : 'text-gray-600'}`}>{c.why}</span>
        </span>
      </Link>
      {c.phone && (
        <>
          <a href={`tel:${c.phone}`} aria-label={`Call ${c.name}`} onClick={() => onCall(c)}
            className="h-11 w-11 flex-none items-center justify-center rounded-full bg-[#0f2340] text-white active:opacity-80 [display:flex]">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M6.6 10.8a15.1 15.1 0 006.6 6.6l2.2-2.2a1 1 0 011-.25 11.4 11.4 0 003.6.57 1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.45.57 3.6a1 1 0 01-.25 1z" /></svg>
          </a>
          <a href={buildWhatsappUrl(c.phone, callListGreeting(c.name))} target="_blank" rel="noopener noreferrer" aria-label={`WhatsApp ${c.name}`}
            className="h-11 w-11 flex-none items-center justify-center rounded-full bg-green-600 text-white active:opacity-80 [display:flex]">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 2a10 10 0 00-8.6 15.1L2 22l5-1.3A10 10 0 1012 2zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2s-1 .3-3.5-.7a12 12 0 01-4.6-4.1 5.2 5.2 0 01-1.1-2.8 3 3 0 011-2.2 1 1 0 01.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.2-.3.3-.1.6a9 9 0 001.6 2 8 8 0 002.4 1.5c.3.1.5.1.6-.1l.9-1.1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3a2.3 2.3 0 01-.3 1z" /></svg>
          </a>
        </>
      )}
    </li>
  )
}

function CallList({ calls, onCall }: { calls: CallItem[]; onCall: (c: CallItem) => void }) {
  const [all, setAll] = React.useState(false)
  if (calls.length === 0) return null
  const shown = all ? calls : calls.slice(0, CALL_LIST_MAX)
  return (
    <section aria-label="Call today" className="rounded-2xl border border-gray-200 bg-white p-4">
      <div className="items-center justify-between [display:flex]">
        <h2 className="font-bold text-gray-900">Call today <span className="font-semibold text-gray-500">· {calls.length}</span></h2>
        <Link href="/studio/leads" className="min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline decoration-[#f0b440] decoration-2 underline-offset-4 [display:flex]">All leads</Link>
      </div>
      <ul className="divide-y divide-gray-100">{shown.map((c) => <CallRow key={c.id} c={c} onCall={onCall} />)}</ul>
      {calls.length > CALL_LIST_MAX && (
        <button type="button" onClick={() => setAll(!all)} className="mt-1 min-h-[44px] w-full text-sm font-semibold text-[#0f2340]">
          {all ? 'Show fewer' : `Show all ${calls.length}`}
        </button>
      )}
    </section>
  )
}

/**
 * After Call on a row, coming back to the app asks how it went: the same log as on the lead (answered moves a new lead to
 * contacted; no answer sets a follow-up for tomorrow), so the call list is right without opening each lead.
 */
function CallLog({ c, onDone }: { c: CallItem; onDone: (logged: boolean) => void }) {
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const log = async (call: 'answered' | 'no_answer') => {
    setBusy(true)
    setError(null)
    try {
      await api.updateLead(c.id, { call })
      onDone(true)
    } catch (e) {
      setError(errorMessage(e))
      setBusy(false)
    }
  }
  return (
    <section aria-label="Log the call" aria-live="polite" className="space-y-2 rounded-2xl border-2 border-[#0f2340] bg-white p-4">
      <p className="font-bold text-gray-900">Called {c.name.split(' ')[0]}? How did it go?</p>
      <div className="grid grid-cols-2 gap-2">
        <button type="button" disabled={busy} onClick={() => log('answered')}
          className="min-h-[48px] rounded-xl bg-[#0f2340] font-semibold text-white disabled:bg-gray-300">Answered</button>
        <button type="button" disabled={busy} onClick={() => log('no_answer')}
          className="min-h-[48px] rounded-xl border border-gray-300 bg-white font-semibold text-[#0f2340] disabled:text-gray-400">No answer</button>
      </div>
      {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
      <div className="items-center justify-between [display:flex]">
        <Link href={`/studio/leads/${c.id}`} className="min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline [display:flex]">Add a note on the lead</Link>
        <button type="button" onClick={() => onDone(false)} className="min-h-[44px] px-2 text-sm font-semibold text-gray-600">Not now</button>
      </div>
    </section>
  )
}

function TodoList({ rows }: { rows: TodoRow[] }) {
  if (rows.length === 0) return null
  return (
    <section aria-label="To do" className="rounded-2xl border border-amber-300 bg-amber-50 p-3">
      <h2 className="px-1 pb-1 font-bold text-amber-950">To do</h2>
      <ul className="divide-y divide-amber-200">
        {rows.map((r) => (
          <li key={r.key}>
            <Link href={r.href} data-testid={`todo-${r.key}`} className="min-h-[52px] items-center gap-3 px-1 font-semibold text-amber-950 [display:flex]">
              <span className="inline-flex h-7 min-w-[28px] flex-none items-center justify-center rounded-full bg-amber-600 px-2 text-sm tabular-nums text-white">{r.n}</span>
              <span className="flex-1">{r.text}</span>
              <span aria-hidden>&rsaquo;</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}

function CaughtUp({ hasListings }: { hasListings: boolean }) {
  return (
    <section aria-label="All caught up" className="rounded-2xl border border-green-200 bg-green-50 p-4">
      <h2 className="font-bold text-green-900">All caught up</h2>
      <p className="mt-1 text-sm text-green-900">
        {hasListings
          ? 'Nobody is waiting for you. A good time to share a listing in your WhatsApp groups or add a new one.'
          : 'Add your first listing and share your website: every buyer who enquires shows up here.'}
      </p>
    </section>
  )
}

/**
 * Studio home, top to bottom: who you are and today's date; Add listing and Share my website; the call list; the to-do list;
 * the setup steps while any is open; this week's numbers. Every list opens its screen already filtered.
 */
export function TodayScreen() {
  const owner = useIsOwner()
  const [shared, setShared] = React.useState(false)
  React.useEffect(() => setShared(siteShared()), [])
  const [siteUrl, setSiteUrl] = React.useState<string | null>(null)
  React.useEffect(() => setSiteUrl(getSiteUrl()), [])
  const { data, loading, reload } = useAsync(() => loadHome(owner), [owner])
  const [called, setCalled] = React.useState<CallItem | null>(null)
  // back from a call or WhatsApp: the lists are read again, quietly
  React.useEffect(() => {
    const onVisible = () => { if (document.visibilityState === 'visible') void reload() }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [reload])
  const onShared = () => {
    markSiteShared()
    setShared(true)
  }

  if (loading && !data) return <Spinner />
  if (!data) return null
  const brand = data.brand
  const steps = setupSteps({
    hasLogo: !!(brand?.branding_data?.logo || brand?.photo),
    hasRera: !!brand?.branding_data?.rera_agent_no,
    listings: data.listings.length,
    shared,
    owner,
  }).filter((s) => !(s.key === 'rera' && reraDue(brand)))   // the RERA reminder above says it, with its date
  const quiet = data.calls.length === 0 && data.todo.length === 0

  return (
    <div className="space-y-4">
      <Header brand={brand} />
      <ReraReminder brand={brand} />
      <QuickActions siteUrl={siteUrl} onShared={onShared} />
      {data.todayError && <ErrorBox message={data.todayError} onRetry={reload} />}
      {called && <CallLog c={called} onDone={(logged) => { setCalled(null); if (logged) void reload() }} />}
      <CallList calls={data.calls} onCall={setCalled} />
      <TodoList rows={data.todo} />
      {/* after the people waiting: a new agent has nobody to call yet, so for them it is at the top anyway */}
      {brand && <SetupCard steps={steps} />}
      {quiet && !data.todayError && <CaughtUp hasListings={data.listings.length > 0} />}
      <WeeklyCard report={data.week} />
    </div>
  )
}
