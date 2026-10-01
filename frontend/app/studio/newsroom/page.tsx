'use client'
import React from 'react'
import { QueueCard } from '@/components/app/newsroom/QueueCard'
import { StatusStrip } from '@/components/app/newsroom/StatusStrip'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { newsroomApi } from '@/lib/app/newsroom'
import type { ApproveBody } from '@/lib/app/newsroom'
import { useAsync } from '@/lib/app/useAsync'

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
