'use client'
import React from 'react'
import { ContentCard } from '@/components/app/content/ContentCard'
import { PostedList } from '@/components/app/content/PostedList'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { contentApi, groupItems } from '@/lib/app/content'
import type { ContentGroup, ContentItem, ContentStatus } from '@/lib/app/content'
import { useAsync } from '@/lib/app/useAsync'

type Data = { upcoming: ContentItem[]; recent: ContentItem[] }

export default function ContentPage() {
  const { data, error, loading, reload, setData } = useAsync<Data>(async () => {
    const [upcoming, recent] = await Promise.all([contentApi.getUpcoming(), contentApi.getRecent(72).catch(() => [] as ContentItem[])])
    return { upcoming, recent }
  }, [])

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null

  const set = (id: string, status: ContentStatus, due_at?: string) =>
    setData((d) => (d ? { ...d, upcoming: d.upcoming.map((i) => (i.id === id ? { ...i, status, ...(due_at ? { due_at } : {}) } : i)) } : d))
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
    setData((d) => (d ? { ...d, upcoming: d.upcoming.filter((i) => i.id !== id) } : d))
  }

  const groups = groupItems(data.upcoming)
  const waiting = groups.filter((g) => g.items.some((i) => i.status === 'planned'))
  const going = groups.filter((g) => !g.items.some((i) => i.status === 'planned'))
  const posted = data.recent.filter((i) => i.status === 'published' || i.status === 'removed')
  const problems = data.recent.filter((i) => i.status === 'failed')
  const cards = (gs: ContentGroup[]) => (
    <ul className="space-y-4">
      {gs.map((g) => <ContentCard key={g.key} group={g} onApprove={approve} onSkip={skip} onPostNow={postNow} />)}
    </ul>
  )

  return (
    <div className="space-y-6">
      <PageTitle>Content</PageTitle>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <p className="text-sm text-gray-600">
        Each card is one post, for Instagram and Facebook. Nothing goes out until you approve it. Approved posts go out at the time shown;
        Post now sends it within a few minutes (several Post now taps go out a few minutes apart).
      </p>

      <section aria-labelledby="waiting-title" className="space-y-3">
        <h2 id="waiting-title" className="text-lg font-bold text-gray-900">Waiting for your OK ({waiting.length})</h2>
        {waiting.length ? cards(waiting) : <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">Nothing is waiting for your OK.</p>}
      </section>

      <section aria-labelledby="going-title" className="space-y-3">
        <h2 id="going-title" className="text-lg font-bold text-gray-900">Going out ({going.length})</h2>
        {going.length ? cards(going) : <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">Nothing approved is waiting to go out.</p>}
      </section>

      {problems.length > 0 && (
        <section aria-labelledby="problems-title" className="space-y-3">
          <h2 id="problems-title" className="text-lg font-bold text-red-800">Problems ({groupItems(problems).length})</h2>
          <PostedList items={problems} kind="problems" />
        </section>
      )}

      <section aria-labelledby="posted-title" className="space-y-3">
        <h2 id="posted-title" className="text-lg font-bold text-gray-900">Posted in the last 3 days ({groupItems(posted).length})</h2>
        <PostedList items={posted} kind="posted" />
      </section>

      <button type="button" onClick={reload} className="min-h-[44px] w-full text-sm font-semibold text-blue-700 underline">Refresh</button>
    </div>
  )
}
