'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { adminApi, CONTROL_TEXT, setupHints } from '@/lib/app/admin'
import type { AdminControls, AdminOverview, ControlFlag, HealthRow } from '@/lib/app/admin'
import { errorMessage } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { useAsync } from '@/lib/app/useAsync'
import { BRAND_NAME } from '@/lib/brand'
import { AddAgentSheet } from '../agents/AddAgentSheet'
import { NavyBtn } from '../agents/InviteRequests'
import { ProgressRing } from '../agents/ProgressRing'
import { Btn, ErrorBox, Spinner } from '../ui'

const NAVY = 'bg-[#102340]'
const GOLD_TEXT = 'text-[#F0B13B]'

function Section({ title, id, children, action }: { title: string; id: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <section aria-labelledby={id} className="space-y-2" data-testid={`admin-${id}`}>
      <div className="flex items-end justify-between">
        <h2 id={id} className="border-b-4 border-[#F0B13B] pb-0.5 text-lg font-extrabold text-[#102340]">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

/** One count tile; the whole tile links to the screen where the numbers come from. */
function Tile({ href, label, today, week, testId }: { href: string; label: string; today: number; week: number; testId: string }) {
  return (
    <Link href={href} data-testid={testId} className="flex min-h-[92px] flex-col justify-between rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50">
      <span className="text-sm font-semibold text-gray-700">{label}</span>
      <span className="text-3xl font-extrabold text-[#102340]">{today}</span>
      <span className="text-xs text-gray-500">{week} in 7 days ›</span>
    </Link>
  )
}

const DOT: Record<HealthRow['status'], string> = { ok: 'bg-green-600', warn: 'bg-amber-500', bad: 'bg-red-600' }
const WORD: Record<HealthRow['status'], string> = { ok: 'OK', warn: 'Check', bad: 'Fix now' }

function HealthItem({ row }: { row: HealthRow }) {
  return (
    <li data-testid="health-row" data-status={row.status} className="flex gap-3 rounded-2xl border border-gray-200 bg-white p-3">
      <span aria-hidden className={`mt-1.5 h-3 w-3 shrink-0 rounded-full ${DOT[row.status]}`} />
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-gray-900">
          {row.label} <span className="sr-only">{WORD[row.status]}</span>
        </p>
        <p className="text-sm text-gray-700">{row.text}</p>
        {row.fix && row.status !== 'ok' && <p className="mt-1 text-xs text-gray-500">Fix: {row.fix}</p>}
        {row.last_run_at && <p className="mt-1 text-xs text-gray-500">Last run {timeAgo(row.last_run_at)}</p>}
      </div>
    </li>
  )
}

const FLAGS: ControlFlag[] = ['posting_paused', 'comments_paused', 'news_paused']

function Controls({ controls, onChange }: { controls: AdminControls; onChange: (c: AdminControls) => void }) {
  const [asking, setAsking] = useState<ControlFlag | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function apply(flag: ControlFlag) {
    setBusy(true)
    setError(null)
    try {
      onChange(await adminApi.setControls({ [flag]: !controls[flag] }))
      setAsking(null)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="space-y-2">
      {error && <ErrorBox message={error} />}
      <ul className="space-y-2">
        {FLAGS.map((flag) => {
          const on = controls[flag]
          const text = CONTROL_TEXT[flag]
          return (
            <li key={flag} className="rounded-2xl border border-gray-200 bg-white p-3" data-testid={`control-${flag}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-gray-900">{text.label}</p>
                  <p className={`text-sm ${on ? 'font-semibold text-amber-700' : 'text-gray-600'}`}>{on ? 'Paused' : 'Running'}</p>
                </div>
                <button type="button" role="switch" aria-checked={on} aria-label={text.label} onClick={() => setAsking(flag)} disabled={busy}
                  className={`relative h-8 w-14 shrink-0 rounded-full transition-colors ${on ? 'bg-amber-500' : 'bg-gray-300'}`}>
                  <span className={`absolute top-1 h-6 w-6 rounded-full bg-white shadow transition-all ${on ? 'left-7' : 'left-1'}`} />
                </button>
              </div>
              {asking === flag && (
                <div className="mt-3 space-y-2 rounded-xl bg-amber-50 p-3" data-testid="control-confirm">
                  <p className="text-sm text-amber-900">{on ? text.resume : text.pause}</p>
                  <div className="flex gap-2">
                    <NavyBtn onClick={() => apply(flag)} disabled={busy}>
                      {busy ? 'Saving...' : on ? `Yes, resume ${text.label.replace('Pause ', '')}` : `Yes, ${text.label.toLowerCase()}`}
                    </NavyBtn>
                    <Btn variant="ghost" onClick={() => setAsking(null)} disabled={busy}>Cancel</Btn>
                  </div>
                </div>
              )}
            </li>
          )
        })}
      </ul>
      {controls.updated_at && <p className="text-xs text-gray-500">Last changed {timeAgo(controls.updated_at)}</p>}
    </div>
  )
}

/** Studio > Admin (owner only): everything the owner runs, on one phone screen. */
export function AdminScreen() {
  const { data, error, loading, reload, setData } = useAsync(() => adminApi.overview(), [])
  const [adding, setAdding] = useState(false)

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  const o = data as AdminOverview
  const t = o.counts.today
  const w = o.counts.week
  const posts = (c: typeof t) => c.posts_published.facebook_page + c.posts_published.instagram
  const nothingWaiting = !o.waiting.posts && !o.waiting.news && !o.invite_requests.length

  return (
    <div className="space-y-6 pb-4" data-testid="admin-screen">
      <header className={`rounded-3xl ${NAVY} px-4 pb-5 pt-5 text-white`}>
        <p className={`text-sm font-semibold ${GOLD_TEXT}`}>{BRAND_NAME} Admin</p>
        <h1 className="text-2xl font-extrabold">Your day at a glance</h1>
        <p className="mt-1 text-xs text-white/70">Updated {timeAgo(o.generated_at)} · <button type="button" className="underline" onClick={reload}>{loading ? 'Refreshing...' : 'Refresh'}</button></p>
        <button type="button" onClick={() => setAdding(true)} data-testid="admin-add-agent"
          className="mt-4 flex min-h-[60px] w-full items-center justify-center rounded-2xl bg-[#F0B13B] text-lg font-extrabold text-[#102340] active:opacity-90">
          + Add agent
        </button>
      </header>

      {error && <ErrorBox message={error} onRetry={reload} />}

      <Section title="Today" id="today">
        <div className="grid grid-cols-2 gap-2">
          <Tile testId="tile-leads" href="/studio/leads" label="New leads" today={t.leads} week={w.leads} />
          <Tile testId="tile-interest" href="/studio/interest" label="Interest taps" today={t.interest_taps} week={w.interest_taps} />
          <Tile testId="tile-chats" href="/studio/interest" label="Chat leads" today={t.chat_leads} week={w.chat_leads} />
          <Tile testId="tile-whatsapp" href="/studio/leads" label="WhatsApp leads" today={t.whatsapp_leads} week={w.whatsapp_leads} />
          <Tile testId="tile-comments" href="/studio/interest" label="Comments answered" today={t.comments_answered} week={w.comments_answered} />
          <Tile testId="tile-posts" href="/studio/content" label="Posts published" today={posts(t)} week={posts(w)} />
          <Tile testId="tile-news" href="/studio/newsroom" label="News published" today={t.news_published} week={w.news_published} />
        </div>
      </Section>

      <Section title="Needs you" id="needs">
        {nothingWaiting && <p className="rounded-2xl bg-white p-4 text-center text-gray-600">Nothing is waiting for you right now.</p>}
        <ul className="space-y-2">
          {o.waiting.posts > 0 && (
            <li><Link href="/studio/content" data-testid="needs-posts" className="flex min-h-[56px] items-center justify-between rounded-2xl border border-gray-200 bg-white p-3">
              <span><b>{o.waiting.posts}</b> {o.waiting.posts === 1 ? 'post waits' : 'posts wait'} for your approval</span><span aria-hidden className="text-xl text-gray-400">›</span>
            </Link></li>
          )}
          {o.waiting.news > 0 && (
            <li><Link href="/studio/newsroom" data-testid="needs-news" className="flex min-h-[56px] items-center justify-between rounded-2xl border border-gray-200 bg-white p-3">
              <span><b>{o.waiting.news}</b> news {o.waiting.news === 1 ? 'story' : 'stories'} to review</span><span aria-hidden className="text-xl text-gray-400">›</span>
            </Link></li>
          )}
          {o.invite_requests.length > 0 && (
            <li><Link href="/studio/agents?tab=asked" data-testid="needs-asked" className="flex min-h-[56px] items-center justify-between rounded-2xl border border-gray-200 bg-white p-3">
              <span><b>{o.invite_requests.length}</b> asked to join on the website</span><span className="text-sm font-semibold text-[#102340]">Agents ›</span>
            </Link></li>
          )}
        </ul>
      </Section>

      <Section title="Agents" id="agents" action={<Link href="/studio/agents" className="text-sm font-semibold text-[#102340] underline">All agents</Link>}>
        {o.agents.length === 0 ? (
          <p className="rounded-2xl bg-white p-4 text-center text-gray-600">No agents yet. Tap + Add agent.</p>
        ) : (
          <ul className="space-y-2">
            {o.agents.map((a) => {
              const hints = setupHints(a)
              return (
                <li key={a.id}>
                  <Link href={`/studio/agents/${encodeURIComponent(a.id)}`} data-testid="admin-agent-row"
                    className="flex min-h-[72px] items-center gap-3 rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50">
                    <ProgressRing done={a.progress.done} total={a.progress.total} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold text-gray-900">{a.name}</p>
                      <p className="truncate text-sm text-gray-600">{a.mobile}{a.listing_count ? ` · ${a.listing_count} live` : ''}{a.last_activity ? ` · ${timeAgo(a.last_activity)}` : ''}</p>
                      <p className="truncate text-xs text-gray-500">{hints.length ? `Finish setup: ${hints.join(', ')}` : 'All set'}</p>
                    </div>
                    <span aria-hidden className="text-xl text-gray-400">›</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        )}
      </Section>

      <Section title="Health" id="health">
        <ul className="space-y-2">{o.health.map((h) => <HealthItem key={h.key} row={h} />)}</ul>
      </Section>

      <Section title="Controls" id="controls">
        <Controls controls={o.controls} onChange={(c) => { setData({ ...o, controls: c }); reload() }} />
      </Section>

      {adding && <AddAgentSheet onClose={() => setAdding(false)} onCreated={reload} />}
    </div>
  )
}
