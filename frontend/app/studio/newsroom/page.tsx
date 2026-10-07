'use client'
import React, { useState } from 'react'
import { TabBar, useUrlTab } from '@/components/app/list'
import { ListRow } from '@/components/app/newsroom/ListRow'
import { QueueCard } from '@/components/app/newsroom/QueueCard'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { friendlyNewsroomError, newsroomApi, tabCounts } from '@/lib/app/newsroom'
import { ApiError } from '@/lib/app/api'
import type { ApproveBody, NewsroomListStatus, NewsroomStatus } from '@/lib/app/newsroom'
import { useAsync } from '@/lib/app/useAsync'
import { BRAND_NAME } from '@/lib/brand'

const TABS = ['review', 'scheduled', 'published', 'rejected']
const LIST_LIMIT = 50

/** One click: the 'New on MahaRERA' carousel and post for the last 30 days, added to To review like any draft. Sits in the title's action slot. */
function MahaReraButton({ onMade, onNote }: { onMade: () => void; onNote: (note: string | null) => void }) {
  const [busy, setBusy] = useState(false)
  async function make() {
    setBusy(true)
    onNote(null)
    try {
      const r = await newsroomApi.mahareraRoundup!()
      const n = `${r.projects} project${r.projects === 1 ? '' : 's'}`
      onNote(r.created ? `MahaRERA post added to To review (${n}). Review it like any draft.` : 'A MahaRERA post is already waiting in To review.')
      onMade()
    } catch (e) {
      // 404 here means 'no project in the last 30 days', not 'item gone': show the server's own words
      onNote(e instanceof ApiError && e.status === 404 ? e.detail : friendlyNewsroomError(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <button type="button" onClick={make} disabled={busy} title="Projects in our areas listed or updated on MahaRERA in the last 30 days: an Instagram carousel and a Facebook post"
      className="min-h-[44px] whitespace-nowrap rounded-xl bg-[#0f2340] px-3 text-sm font-semibold text-white disabled:opacity-60">
      {busy ? 'Making…' : '+ MahaRERA post'}
    </button>
  )
}

/** Off banner and the last run's problem: the only parts of the old status strip that still need saying. */
function Notices({ status }: { status: NewsroomStatus }) {
  return (
    <>
      {!status.enabled && (
        <p role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
          The newsroom is switched off, so no new drafts are being written. Ask your {BRAND_NAME} admin to turn it on.
        </p>
      )}
      {status.last_error && (
        <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-800">
          <span className="font-semibold">The last run had a problem: </span>
          {status.last_error}
        </p>
      )}
    </>
  )
}

const EMPTY: Record<NewsroomListStatus, string> = {
  scheduled: 'Nothing approved is waiting to go out.',
  published: 'Nothing posted yet.',
  rejected: 'Nothing rejected.',
}

export default function NewsroomPage() {
  const { data, error, loading, reload, setData } = useAsync(async () => {
    const [queue, status] = await Promise.all([newsroomApi.getQueue(), newsroomApi.getStatus()])
    return { queue, status }
  }, [])
  const [tab, setTab] = useUrlTab('tab', 'review', TABS)
  const listTab = tab === 'review' ? null : (tab as NewsroomListStatus)
  const list = useAsync(async () => (listTab ? newsroomApi.list(listTab, LIST_LIMIT) : null), [listTab])
  const [openId, setOpenId] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null

  const counts = tabCounts(data.status.counts)
  /** Take the item out of To review and move its count to where it went. */
  const drop = (id: string, to: 'approved' | 'rejected') =>
    setData((d) => {
      if (!d) return d
      const c = d.status.counts
      return {
        queue: d.queue.filter((i) => i.id !== id),
        status: { ...d.status, counts: { ...c, pending_review: Math.max(0, (c.pending_review ?? 0) - 1), [to]: (c[to] ?? 0) + 1 } },
      }
    })

  async function approve(id: string, body: ApproveBody) {
    await newsroomApi.approve(id, body)
    setOpenId(null)
    drop(id, 'approved')
  }
  async function reject(id: string, reason?: string) {
    await newsroomApi.reject(id, reason)
    setOpenId(null)
    drop(id, 'rejected')
  }
  const refresh = () => { reload(); if (listTab) list.reload() }
  const empty = (text: string) => <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">{text}</p>

  return (
    <div className="space-y-3 pb-24">
      <PageTitle action={typeof newsroomApi.mahareraRoundup === 'function'
        ? <MahaReraButton onNote={setNote} onMade={() => { setTab('review'); reload() }} />
        : undefined}>
        Newsroom
      </PageTitle>
      {note && <p role="status" className="rounded-xl bg-blue-50 p-3 text-sm text-gray-800">{note}</p>}
      <TabBar label="Newsroom" value={tab} onChange={(k) => { setTab(k); setOpenId(null) }} tabs={[
        { key: 'review', label: 'To review', count: counts.review, tone: 'urgent' },
        { key: 'scheduled', label: 'Scheduled', count: counts.scheduled },
        { key: 'published', label: 'Published', count: counts.published },
        { key: 'rejected', label: 'Rejected', count: counts.rejected },
      ]} />
      {error && <ErrorBox message={error} onRetry={reload} />}
      <Notices status={data.status} />

      {tab === 'review' && (
        <>
          <p className="text-xs text-gray-600">
            Drafts written from public sources. Tap one to read it, check the facts, then approve or reject. Nothing is posted until you approve.
            {' '}{data.status.last_run_at ? `Last run ${timeAgo(data.status.last_run_at)}.` : 'It has not run yet.'}
          </p>
          {data.queue.length === 0 ? (
            empty(data.status.enabled ? 'Nothing to review right now. New drafts appear here as they are written.' : 'Nothing to review. The newsroom is off.')
          ) : (
            <ul className="space-y-2 p-0">
              {data.queue.map((item) => (
                <QueueCard key={item.id} item={item} onApprove={approve} onReject={reject}
                  open={openId === item.id} onToggle={() => setOpenId((o) => (o === item.id ? null : item.id))}
                  onPreview={typeof newsroomApi.preview === 'function' ? (id, text) => newsroomApi.preview(id, text) : undefined} />
              ))}
            </ul>
          )}
        </>
      )}

      {listTab && (
        list.loading ? <Spinner /> :
        list.error ? <ErrorBox message={list.error} onRetry={list.reload} /> :
        !list.data || list.data.length === 0 ? empty(EMPTY[listTab]) : (
          <ul className="space-y-2 p-0" aria-label={listTab}>
            {list.data.map((item) => <ListRow key={item.id} item={item} />)}
          </ul>
        )
      )}

      <button type="button" onClick={refresh} className="min-h-[44px] w-full text-sm font-semibold text-[#0f2340] underline">Refresh</button>
    </div>
  )
}
