'use client'
import React from 'react'
import Link from 'next/link'
import { sourceLabel } from '@/lib/app/leads'
import { aboutLine, getLive, pageLabel, readTime, type Live, type LiveStory, type LiveVisitor } from '@/lib/app/live'

/**
 * Studio > Results, top: who is on the site right now, today's reading so far and the story of each of today's visits
 * (docs/plan/site-live-presence.md D2, D6). Refreshes every 15 s while Studio is the visible tab; a failed refresh keeps the last
 * good numbers. Watch only: an anonymous visitor cannot be messaged (plan D4), so nothing here reaches out to them.
 * Your own browsers (signed in to Studio) show as "You" and are never counted.
 */
export const REFRESH_MS = 15_000
const STORIES = 10

function useLive(): { live: Live | null; failed: boolean } {
  const [live, setLive] = React.useState<Live | null>(null)
  const [failed, setFailed] = React.useState(false)
  React.useEffect(() => {
    let alive = true
    const load = () => {
      if (document.visibilityState === 'hidden') return
      getLive().then((d) => { if (alive) { setLive(d); setFailed(false) } }, () => { if (alive) setFailed(true) })
    }
    load()
    const timer = window.setInterval(load, REFRESH_MS)
    document.addEventListener('visibilitychange', load)
    return () => {
      alive = false
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', load)
    }
  }, [])
  return { live, failed }
}

const fromLabel = (key: string) => sourceLabel(key) || 'Direct'

function Steps({ steps }: { steps: Array<{ page: string; at?: string; read_s?: number | null }> }) {
  return (
    <ol className="space-y-1 text-sm">
      {steps.map((s, i) => (
        <li key={i} className="flex justify-between gap-2">
          <span className="flex min-w-0 gap-2">
            {s.at && <span className="shrink-0 tabular-nums text-gray-500">{s.at}</span>}
            <a href={s.page} target="_blank" rel="noopener noreferrer" className="min-w-0 truncate text-blue-700 underline">{pageLabel(s.page)}</a>
          </span>
          <span className="shrink-0 tabular-nums text-gray-500">{readTime(s.read_s)}</span>
        </li>
      ))}
    </ol>
  )
}

function Visitor({ v }: { v: LiveVisitor }) {
  const [open, setOpen] = React.useState(false)
  const you = v.who.kind === 'you'
  const about = aboutLine(v)
  return (
    <li className={'px-3 py-2 ' + (you ? 'bg-gray-50' : '')}>
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="flex min-h-[44px] w-full items-start gap-2 text-left">
        <span aria-hidden className={'mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ' + (v.reading && !you ? 'bg-green-600' : 'bg-gray-300')} />
        <span className="min-w-0 flex-1">
          <span className={'block truncate font-semibold ' + (you ? 'text-gray-500' : 'text-gray-900')}>{pageLabel(v.page)}</span>
          <span className="block text-sm text-gray-600">
            {v.who.label} · {v.pages} page{v.pages === 1 ? '' : 's'} · {v.minutes ? `${v.minutes} min` : 'just came'} · from {fromLabel(v.came_from)}
            {!v.reading && ' · tab open'}
          </span>
          {about && <span className="block text-xs text-gray-500">{about}</span>}
        </span>
        <span aria-hidden className="mt-1 text-gray-400">{open ? '▴' : '▾'}</span>
      </button>
      {open && (
        <div className="ml-4 mt-1 space-y-1 border-l-2 border-gray-100 pl-3">
          <Steps steps={v.journey} />
          {v.who.lead_id && <Link href={`/studio/leads/${v.who.lead_id}`} className="inline-flex min-h-[44px] items-center text-sm font-semibold text-blue-700">Open lead</Link>}
        </div>
      )}
    </li>
  )
}

function Story({ s }: { s: LiveStory }) {
  const [open, setOpen] = React.useState(false)
  const you = s.who.kind === 'you'
  const about = aboutLine(s)
  const time = s.start === s.end ? s.start : `${s.start}–${s.end}`
  return (
    <li className={'px-3 py-2 ' + (you ? 'bg-gray-50' : '')}>
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="flex min-h-[44px] w-full items-start gap-2 text-left">
        <span className="w-[5.5rem] shrink-0 pt-0.5 text-sm tabular-nums text-gray-500">{time}</span>
        <span className="min-w-0 flex-1">
          <span className={'block truncate font-semibold ' + (you ? 'text-gray-500' : 'text-gray-900')}>
            {s.who.label} · from {fromLabel(s.came_from)}{s.here_now && <span className="ml-1 text-xs font-semibold text-green-700">here now</span>}
          </span>
          <span className="block text-sm text-gray-600">
            {s.pages} page{s.pages === 1 ? '' : 's'}{s.read_s ? ` · read ${readTime(s.read_s)}` : ''} · first: {pageLabel(s.landing)}
          </span>
          {about && <span className="block text-xs text-gray-500">{about}</span>}
          {s.did.length > 0 && (
            <span className="mt-1 flex flex-wrap gap-1">
              {s.did.map((d, i) => <span key={i} className="rounded-full bg-green-50 px-2 py-0.5 text-xs font-semibold text-green-800">{d.what}</span>)}
            </span>
          )}
        </span>
        <span aria-hidden className="mt-1 text-gray-400">{open ? '▴' : '▾'}</span>
      </button>
      {open && (
        <div className="ml-4 mt-1 space-y-2 border-l-2 border-gray-100 pl-3">
          <Steps steps={s.steps} />
          {s.did.length > 0 && (
            <ul className="space-y-1 text-sm text-gray-700">
              {s.did.map((d, i) => <li key={i}><span className="tabular-nums text-gray-500">{d.at}</span> {d.what}</li>)}
            </ul>
          )}
          {s.who.lead_id && <Link href={`/studio/leads/${s.who.lead_id}`} className="inline-flex min-h-[44px] items-center text-sm font-semibold text-blue-700">Open lead</Link>}
        </div>
      )}
    </li>
  )
}

function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-3">
      <p className="text-2xl font-bold tabular-nums text-gray-900">{value}</p>
      <p className="text-sm font-semibold text-gray-700">{label}</p>
    </div>
  )
}

function Stories({ stories }: { stories: LiveStory[] }) {
  const [all, setAll] = React.useState(false)
  if (stories.length === 0) return null
  return (
    <section aria-label="Today's visitors" className="space-y-2">
      <h2 className="text-lg font-bold">Today&apos;s visitors</h2>
      <p className="text-sm text-gray-600">Newest first, India time. Tap one to see the pages they read and what they did.</p>
      <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-200 bg-white">
        {(all ? stories : stories.slice(0, STORIES)).map((s, i) => <Story key={`${s.who.label}-${s.start}-${i}`} s={s} />)}
      </ul>
      {stories.length > STORIES && (
        <button type="button" onClick={() => setAll(!all)} className="min-h-[44px] w-full text-center text-sm font-semibold text-blue-700">
          {all ? 'Show less' : `See all ${stories.length}`}
        </button>
      )}
      <p className="text-xs text-gray-500">
        Area and network are approximate (phones are often routed through Mumbai). We do not keep anyone&apos;s internet address.{' '}
        <a href="https://db-ip.com" target="_blank" rel="noopener noreferrer" className="underline">IP Geolocation by DB-IP</a>
      </p>
    </section>
  )
}

export default function LiveNow() {
  const { live, failed } = useLive()
  if (!live) return failed ? <p className="text-sm text-gray-500">Could not load who is on the site. Trying again…</p> : null
  const { now, today } = live
  const you = now.visitors.some((v) => v.who.kind === 'you')
  return (
    <>
      <section aria-label="Right now" className="space-y-2">
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <span aria-hidden className={'h-2.5 w-2.5 rounded-full ' + (now.count ? 'bg-green-600' : 'bg-gray-300')} />
          Right now
        </h2>
        {now.count === 0 && <p className="rounded-2xl border border-gray-200 bg-white p-3 text-sm text-gray-600">Nobody else is on the site this minute.</p>}
        {now.count > 0 && <p className="text-sm text-gray-600">{now.count} {now.count === 1 ? 'person is' : 'people are'} on the site. Tap one to see the pages they read.</p>}
        {now.visitors.length > 0 && (
          <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-200 bg-white">
            {now.visitors.map((v) => <Visitor key={v.who.lead_id ?? v.who.label} v={v} />)}
          </ul>
        )}
        {you && <p className="text-xs text-gray-500">&quot;You&quot; is a browser signed in to Studio: shown, never counted.</p>}
        {failed && <p className="text-xs text-gray-500">Last refresh failed; showing the numbers from before.</p>}
      </section>
      <section aria-label="Today on the site" className="space-y-2">
        <h2 className="text-sm font-semibold text-gray-600">Today on the site (not counting you)</h2>
        <div className="grid grid-cols-3 gap-2">
          <Stat value={today.visitors} label="Visitors" />
          <Stat value={today.pages} label="Pages read" />
          <Stat value={readTime(today.avg_read_s) || '–'} label="Per page" />
        </div>
        {today.visits > 0 && (
          <p className="text-sm text-gray-600">{today.one_page_visits} of {today.visits} visit{today.visits === 1 ? '' : 's'} read only one page.</p>
        )}
        {today.top_pages.length > 0 && (
          <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-200 bg-white">
            <li className="grid grid-cols-[1fr_3.5rem_4.5rem] gap-2 px-3 py-2 text-xs font-semibold text-gray-500">
              <span>Most read</span><span className="text-right">Views</span><span className="text-right">Per view</span>
            </li>
            {today.top_pages.map((p) => (
              <li key={p.page} className="grid grid-cols-[1fr_3.5rem_4.5rem] items-center gap-2 px-3 py-2 text-sm">
                <a href={p.page} target="_blank" rel="noopener noreferrer" className="min-w-0 truncate text-gray-900 underline decoration-gray-300">{pageLabel(p.page)}</a>
                <span className="text-right tabular-nums">{p.views}</span>
                <span className="text-right tabular-nums text-gray-600">{readTime(p.avg_read_s) || '–'}</span>
              </li>
            ))}
          </ul>
        )}
        {today.left_from.length > 0 && (
          <p className="text-sm text-gray-600">
            Most left from: {today.left_from.map((p) => `${pageLabel(p.page)} (${p.visits})`).join(', ')}
          </p>
        )}
      </section>
      <Stories stories={today.stories ?? []} />
    </>
  )
}
