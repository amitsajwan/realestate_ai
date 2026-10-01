'use client'
import React from 'react'
import { ContentCard } from '@/components/app/content/ContentCard'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { contentApi } from '@/lib/app/content'
import { useAsync } from '@/lib/app/useAsync'

export default function ContentPage() {
  const { data, error, loading, reload, setData } = useAsync(() => contentApi.getUpcoming(), [])

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null

  async function approve(id: string) {
    await contentApi.approve(id)
    setData((d) => (d ? d.map((i) => (i.id === id ? { ...i, status: 'approved' } : i)) : d))
  }
  async function skip(id: string) {
    await contentApi.skip(id)
    setData((d) => (d ? d.filter((i) => i.id !== id) : d))
  }
  const waiting = data.filter((i) => i.status === 'planned').length

  return (
    <div className="space-y-4">
      <PageTitle>Content</PageTitle>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <p className="text-sm text-gray-600">
        The planned posts, in date order. Nothing is posted until you approve it. {waiting > 0 ? `${waiting} waiting for your OK.` : 'Nothing is waiting for your OK.'}
      </p>
      {data.length === 0 ? (
        <p className="rounded-2xl bg-white p-6 text-center text-gray-600">No upcoming posts. Ask for a new plan.</p>
      ) : (
        <ul className="space-y-4">
          {data.map((item) => (
            <ContentCard key={item.id} item={item} onApprove={approve} onSkip={skip} />
          ))}
        </ul>
      )}
      <button type="button" onClick={reload} className="min-h-[44px] w-full text-sm font-semibold text-blue-700 underline">Refresh</button>
    </div>
  )
}
