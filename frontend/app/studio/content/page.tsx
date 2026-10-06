'use client'
import React from 'react'
import { ContentCard } from '@/components/app/content/ContentCard'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { contentApi, groupItems } from '@/lib/app/content'
import type { ContentStatus } from '@/lib/app/content'
import { useAsync } from '@/lib/app/useAsync'

export default function ContentPage() {
  const { data, error, loading, reload, setData } = useAsync(() => contentApi.getUpcoming(), [])

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null

  const set = (id: string, status: ContentStatus, due_at?: string) =>
    setData((d) => (d ? d.map((i) => (i.id === id ? { ...i, status, ...(due_at ? { due_at } : {}) } : i)) : d))
  async function approve(id: string) {
    await contentApi.approve(id)
    set(id, 'approved')
  }
  async function postNow(id: string) {
    await contentApi.postNow(id)
    set(id, 'approved', new Date().toISOString())
  }
  async function skip(id: string) {
    await contentApi.skip(id)
    setData((d) => (d ? d.filter((i) => i.id !== id) : d))
  }
  const groups = groupItems(data)
  const waiting = groups.filter((g) => g.items.some((i) => i.status === 'planned')).length

  return (
    <div className="space-y-4">
      <PageTitle>Content</PageTitle>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <p className="text-sm text-gray-600">
        Each card is one post, for Instagram and Facebook. Nothing goes out until you approve it; approved posts go out at the time shown,
        or tap Post now to send it within a few minutes. {waiting > 0 ? `${waiting} waiting for your OK.` : 'Nothing is waiting for your OK.'}
      </p>
      {groups.length === 0 ? (
        <p className="rounded-2xl bg-white p-6 text-center text-gray-600">No upcoming posts. Ask for a new plan.</p>
      ) : (
        <ul className="space-y-4">
          {groups.map((g) => (
            <ContentCard key={g.key} group={g} onApprove={approve} onSkip={skip} onPostNow={postNow} />
          ))}
        </ul>
      )}
      <button type="button" onClick={reload} className="min-h-[44px] w-full text-sm font-semibold text-blue-700 underline">Refresh</button>
    </div>
  )
}
