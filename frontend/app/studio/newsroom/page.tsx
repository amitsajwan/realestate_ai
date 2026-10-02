'use client'
import React from 'react'
import { QueueCard } from '@/components/app/newsroom/QueueCard'
import { StatusStrip } from '@/components/app/newsroom/StatusStrip'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { friendlyNewsroomError, newsroomApi } from '@/lib/app/newsroom'
import { ApiError } from '@/lib/app/api'
import type { ApproveBody } from '@/lib/app/newsroom'
import { useAsync } from '@/lib/app/useAsync'

/** One click: the 'New on MahaRERA' carousel and post for the last 30 days, added to the queue for review like any draft. */
function MahaReraButton({ onMade }: { onMade: () => void }) {
  const [busy, setBusy] = React.useState(false)
  const [note, setNote] = React.useState<string | null>(null)
  async function make() {
    setBusy(true)
    setNote(null)
    try {
      const r = await newsroomApi.mahareraRoundup!()
      const n = `${r.projects} project${r.projects === 1 ? '' : 's'}`
      setNote(r.created ? `Added to the queue below (${n}). Review it like any draft.` : 'One is already waiting for review below.')
      onMade()
    } catch (e) {
      // 404 here means 'no project in the last 30 days', not 'item gone': show the server's own words
      setNote(e instanceof ApiError && e.status === 404 ? e.detail : friendlyNewsroomError(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="rounded-2xl bg-white p-4">
      <button type="button" onClick={make} disabled={busy}
        className="min-h-[44px] w-full rounded-xl bg-blue-700 px-4 text-sm font-semibold text-white disabled:opacity-60">
        {busy ? 'Making the post…' : 'Make the MahaRERA post (last 30 days)'}
      </button>
      <p className="mt-2 text-xs text-gray-600">Projects in Kharadi and Wagholi listed or updated on MahaRERA: an Instagram carousel and a Facebook post.</p>
      {note && <p role="status" className="mt-2 text-sm text-gray-800">{note}</p>}
    </div>
  )
}

export default function NewsroomPage() {
  const { data, error, loading, reload, setData } = useAsync(async () => {
    const [queue, status] = await Promise.all([newsroomApi.getQueue(), newsroomApi.getStatus()])
    return { queue, status }
  }, [])

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null

  const drop = (id: string) =>
    setData((d) => (d ? { queue: d.queue.filter((i) => i.id !== id), status: { ...d.status, counts: { ...d.status.counts, pending_review: Math.max(0, (d.status.counts.pending_review ?? 0) - 1) } } } : d))

  async function approve(id: string, body: ApproveBody) {
    await newsroomApi.approve(id, body)
    drop(id)
  }
  async function reject(id: string, reason?: string) {
    await newsroomApi.reject(id, reason)
    drop(id)
  }

  return (
    <div className="space-y-4">
      <PageTitle>Newsroom</PageTitle>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <StatusStrip status={data.status} />
      {typeof newsroomApi.mahareraRoundup === 'function' && <MahaReraButton onMade={reload} />}
      <p className="text-sm text-gray-600">Drafts written from public sources. Read, edit if you like, then approve or reject. Nothing is posted until you approve.</p>
      {data.queue.length === 0 ? (
        <p className="rounded-2xl bg-white p-6 text-center text-gray-600">
          {data.status.enabled ? 'Nothing to review right now. New drafts appear here as they are written.' : 'Nothing to review. The newsroom is off.'}
        </p>
      ) : (
        <ul className="space-y-4">
          {data.queue.map((item) => (
            <QueueCard key={item.id} item={item} onApprove={approve} onReject={reject}
              onPreview={typeof newsroomApi.preview === 'function' ? (id, text) => newsroomApi.preview(id, text) : undefined} />
          ))}
        </ul>
      )}
      <button type="button" onClick={reload} className="min-h-[44px] w-full text-sm font-semibold text-blue-700 underline">Refresh</button>
    </div>
  )
}
