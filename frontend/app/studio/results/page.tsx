'use client'
import React from 'react'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { getInterestReport, type InterestLinkStats } from '@/lib/app/interestReport'
import { sourceLabel } from '@/lib/app/leads'
import { getOrigins, type OriginRow } from '@/lib/app/origins'
import { t } from '@/lib/app/strings'
import type { FacebookStatus } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'
import { BRAND_NAME } from '@/lib/brand'

/**
 * Studio > Results (replaced Interest, 2026-10-17): one question, "is my marketing working?". Three numbers for the last 7 days
 * against the 7 before, where people came from and the posts that brought leads, five rows each with "See all".
 * What people said is in the Inbox (chats and comments), not here.
 */
const TOP = 5
type Totals = { visitors: number; chats: number; leads: number }

const sum = (rows: OriginRow[]): Totals =>
  rows.reduce((a, r) => ({ visitors: a.visitors + r.visitors, chats: a.chats + r.chats, leads: a.leads + r.leads }), { visitors: 0, chats: 0, leads: 0 })

function Delta({ now, before }: { now: number; before: number }) {
  const d = now - before
  if (d === 0) return <span className="text-xs text-gray-500">same as last week</span>
  const up = d > 0
  const pct = before > 0 && Math.abs(d) >= 10 ? ` (${Math.round((Math.abs(d) / before) * 100)}%)` : ''
  return <span className={'text-xs font-semibold ' + (up ? 'text-green-700' : 'text-red-700')}>{up ? '▲' : '▼'} {Math.abs(d)}{pct} vs last week</span>
}

function Tile({ label, now, before }: { label: string; now: number; before: number }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-3">
      <p className="text-2xl font-bold tabular-nums text-gray-900">{now}</p>
      <p className="text-sm font-semibold text-gray-700">{label}</p>
      <Delta now={now} before={before} />
    </div>
  )
}

function SeeAll({ open, total, onClick }: { open: boolean; total: number; onClick: () => void }) {
  if (total <= TOP) return null
  return (
    <button type="button" onClick={onClick} className="min-h-[44px] w-full text-center text-sm font-semibold text-blue-700">
      {open ? 'Show less' : `See all ${total}`}
    </button>
  )
}

function WhereFrom({ rows }: { rows: OriginRow[] }) {
  const [open, setOpen] = React.useState(false)
  const sorted = [...rows].sort((a, b) => Number(a.source === 'unknown') - Number(b.source === 'unknown') || b.visitors - a.visitors || b.leads - a.leads)
  if (sorted.length === 0) return null
  return (
    <section aria-label="Where they came from" className="space-y-2">
      <h2 className="text-lg font-bold">Where they came from</h2>
      <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-200 bg-white">
        <li className="grid grid-cols-[1fr_4.5rem_3.5rem] gap-2 px-3 py-2 text-xs font-semibold text-gray-500">
          <span>From</span><span className="text-right">Visitors</span><span className="text-right">Leads</span>
        </li>
        {(open ? sorted : sorted.slice(0, TOP)).map((r) => {
          const post = (r.posts ?? []).find((p) => !p.removed)
          return (
            <li key={r.source} className={'grid grid-cols-[1fr_4.5rem_3.5rem] items-center gap-2 px-3 py-2 text-sm ' + (r.source === 'unknown' ? 'text-gray-500' : 'text-gray-900')}>
              <span className="min-w-0">
                <span className="block truncate font-medium">{sourceLabel(r.source)}</span>
                {post && <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-xs font-semibold text-blue-700 underline">Open {post.kind === 'reel' ? 'reel' : 'post'}</a>}
              </span>
              <span className="text-right tabular-nums">{r.visitors}</span>
              <span className="text-right font-semibold tabular-nums">{r.leads}</span>
            </li>
          )
        })}
      </ul>
      <SeeAll open={open} total={sorted.length} onClick={() => setOpen(!open)} />
      <p className="text-xs text-gray-500">Direct = opened inside an app that hides where from (WhatsApp, Instagram) or typed in.</p>
    </section>
  )
}

function BestPosts({ links }: { links: InterestLinkStats[] }) {
  const [open, setOpen] = React.useState(false)
  const shown = links.filter((l) => l.clicks || l.leads_with_phone)
    .sort((a, b) => b.leads_with_phone - a.leads_with_phone || b.clicks - a.clicks)
  if (shown.length === 0) return null
  return (
    <section aria-label="Best posts" className="space-y-2">
      <h2 className="text-lg font-bold">Best posts</h2>
      <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-200 bg-white">
        {(open ? shown : shown.slice(0, TOP)).map((l) => (
          <li key={l.code} className="px-3 py-2">
            <p className="truncate font-semibold text-gray-900">{l.title || l.ref}</p>
            <p className="text-sm text-gray-600">
              {sourceLabel(l.channel)} · {l.clicks} visit{l.clicks === 1 ? '' : 's'} ·{' '}
              <span className={l.leads_with_phone ? 'font-semibold text-green-800' : ''}>{l.leads_with_phone} lead{l.leads_with_phone === 1 ? '' : 's'}</span>
            </p>
          </li>
        ))}
      </ul>
      <SeeAll open={open} total={shown.length} onClick={() => setOpen(!open)} />
    </section>
  )
}

export default function ResultsPage() {
  const { data, error, loading, reload } = useAsync(async () => {
    const [week, fortnight, links, fb] = await Promise.all([
      getOrigins(7),
      getOrigins(14).catch(() => null),
      getInterestReport().catch(() => [] as InterestLinkStats[]),
      api.getFacebookStatus().catch(() => null as FacebookStatus | null),
    ])
    return { week, fortnight, links, fb }
  }, [])
  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null
  const now = sum(data.week.rows)
  const both = data.fortnight ? sum(data.fortnight.rows) : now
  const before = { visitors: both.visitors - now.visitors, chats: both.chats - now.chats, leads: both.leads - now.leads }
  return (
    <div className="space-y-5">
      <PageTitle>{t('results')}</PageTitle>
      {(data.fb?.reconnect || data.fb?.instagram?.reconnect) && (
        <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-800">The Facebook connection has stopped working, so comments are not being answered right now. Ask your {BRAND_NAME} admin to reconnect it.</p>
      )}
      <section aria-label="Last 7 days" className="space-y-2">
        <h2 className="text-sm font-semibold text-gray-600">Last 7 days</h2>
        <div className="grid grid-cols-3 gap-2">
          <Tile label="Visitors" now={now.visitors} before={before.visitors} />
          <Tile label="Chats" now={now.chats} before={before.chats} />
          <Tile label="Leads" now={now.leads} before={before.leads} />
        </div>
      </section>
      <WhereFrom rows={data.week.rows} />
      <BestPosts links={data.links} />
    </div>
  )
}
