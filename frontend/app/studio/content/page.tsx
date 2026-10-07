'use client'
import React, { useState } from 'react'
import { CampaignCard } from '@/components/app/content/CampaignCard'
import { ContentCard } from '@/components/app/content/ContentCard'
import { TYPE_FILTERS, TypeChips } from '@/components/app/content/TypeChips'
import type { TypeFilter } from '@/components/app/content/TypeChips'
import { PostedList } from '@/components/app/content/PostedList'
import { ConfirmSheet, TabBar, UndoBar, useUndo, useUrlTab } from '@/components/app/list'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { contentApi, foldCampaigns, groupItems, ofType, typeCounts, typeLabel } from '@/lib/app/content'
import type { ContentGroup, ContentItem, ContentStatus } from '@/lib/app/content'
import { useAsync } from '@/lib/app/useAsync'

type Data = { upcoming: ContentItem[]; recent: ContentItem[] }
const TABS = ['approve', 'going', 'problems', 'posted']

export default function ContentPage() {
  const { data, error, loading, reload, setData } = useAsync<Data>(async () => {
    const [upcoming, recent] = await Promise.all([contentApi.getUpcoming(), contentApi.getRecent(72).catch(() => [] as ContentItem[])])
    return { upcoming, recent }
  }, [])
  const [openKey, setOpenKey] = useState<string | null>(null)
  const [bulk, setBulk] = useState(false)
  const [bulkBusy, setBulkBusy] = useState(false)
  const [pending, schedule, undo] = useUndo(8000)

  const groups = groupItems(data?.upcoming ?? [])
  const skipping = new Set(pending ? pending.id.split(',') : [])
  const visible = groups.map((g) => ({ ...g, items: g.items.filter((i) => !skipping.has(i.id)) })).filter((g) => g.items.length)
  const waiting = visible.filter((g) => g.items.some((i) => i.status === 'planned'))
  const going = visible.filter((g) => !g.items.some((i) => i.status === 'planned'))
  const recent = data?.recent ?? []
  const posted = recent.filter((i) => i.status === 'published' || i.status === 'removed')
  const problems = groupItems(recent.filter((i) => i.status === 'failed'))
  const [tab, setTab] = useUrlTab('tab', waiting.length ? 'approve' : 'going', TABS)
  const [type, setType] = useUrlTab('type', 'all', TYPE_FILTERS) as [TypeFilter, (k: string) => void]
  const inTab = tab === 'approve' ? waiting : tab === 'going' ? going : tab === 'problems' ? problems : groupItems(posted)
  const shown = ofType(inTab, type)

  if (loading && !data) return <Spinner />
  if (error && !data) return <ErrorBox message={error} onRetry={reload} />
  if (!data) return null

  const set = (id: string, status: ContentStatus, due_at?: string) =>
    setData((d) => (d ? { ...d, upcoming: d.upcoming.map((i) => (i.id === id ? { ...i, status, ...(due_at ? { due_at } : {}) } : i)) } : d))
  const approve = async (id: string) => { await contentApi.approve(id); set(id, 'approved') }
  const postNow = async (id: string) => { await contentApi.postNow(id); set(id, 'approved', new Date().toISOString()) }
  const unapprove = async (id: string) => { await contentApi.unapprove(id); set(id, 'planned') }
  const retry = async (id: string) => { await contentApi.retry(id); await reload() }
  const skip = (ids: string[]) => {
    setOpenKey(null)
    schedule(ids.join(','), 'Skipped. It will not be posted.', async () => {
      for (const id of ids) await contentApi.skip(id)
      setData((d) => (d ? { ...d, upcoming: d.upcoming.filter((i) => !ids.includes(i.id)) } : d))
    })
  }
  const approveAll = async () => {
    setBulkBusy(true)
    try {
      for (const g of shown) for (const i of g.items.filter((x) => x.status === 'planned')) await approve(i.id)
    } finally {
      setBulkBusy(false)
      setBulk(false)
    }
  }

  const toggle = (key: string) => () => setOpenKey((k) => (k === key ? null : key))
  const actions = { onApprove: approve, onSkip: skip, onPostNow: postNow, onUnapprove: unapprove, onRetry: retry }
  const cards = (gs: ContentGroup[]) => (
    <ul className="space-y-2 p-0">
      {foldCampaigns(gs).map((r) => r.type === 'campaign'
        ? <CampaignCard key={r.key} title={r.title} groups={r.groups} open={openKey === r.key} onToggle={toggle(r.key)} {...actions} />
        : <ContentCard key={r.key} group={r.group} open={openKey === r.key} onToggle={toggle(r.key)} {...actions} />)}
    </ul>
  )
  const none = (text: string) => empty(type === 'all' ? text : `No ${typeLabel(type).toLowerCase()} here.`)
  function empty(text: string) {
    return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">{text}</p>
  }

  return (
    <div className="space-y-3 pb-24">
      <PageTitle action={<button type="button" onClick={reload} className="min-h-[44px] px-2 text-sm font-semibold text-[#0f2340] underline">Refresh</button>}>
        Content
      </PageTitle>
      <TabBar label="Content" value={tab} onChange={(k) => { setTab(k); setOpenKey(null) }} tabs={[
        { key: 'approve', label: 'To approve', count: waiting.length, tone: 'urgent' },
        { key: 'going', label: 'Going out', count: going.length },
        { key: 'problems', label: 'Problems', count: problems.length, tone: 'error', hideWhenEmpty: true },
        { key: 'posted', label: 'Posted', count: groupItems(posted).length },
      ]} />
      {error && <ErrorBox message={error} onRetry={reload} />}
      <TypeChips counts={typeCounts(inTab)} value={type} onChange={(t) => { setType(t); setOpenKey(null) }} />
      <p className="text-xs text-gray-600">Nothing goes out until you approve it. Tap a post to see it in full.</p>

      {tab === 'approve' && (shown.length ? cards(shown) : none('Nothing is waiting for your OK. Approved posts are under Going out.'))}
      {tab === 'going' && (shown.length ? cards(shown) : none('Nothing approved is waiting to go out.'))}
      {tab === 'problems' && (shown.length ? cards(shown) : none('No problems.'))}
      {tab === 'posted' && <PostedList items={posted.filter((i) => type === 'all' || i.group === type)} kind="posted" />}

      {tab === 'approve' && shown.length > 1 && (
        <div className="fixed inset-x-0 z-40 border-t border-gray-200 bg-white/95 px-4 py-2 backdrop-blur" style={{ bottom: 'calc(60px + env(safe-area-inset-bottom, 0px))' }}>
          <button type="button" onClick={() => setBulk(true)} className="mx-auto block min-h-[48px] w-full max-w-md rounded-xl bg-[#0f2340] text-base font-semibold text-white">
            Approve all {shown.length}{type === 'all' ? '' : ` ${typeLabel(type).toLowerCase()}`}
          </button>
        </div>
      )}
      {bulk && (
        <ConfirmSheet title={`Approve all ${shown.length} ${type === 'all' ? 'posts' : typeLabel(type).toLowerCase()}?`} confirmLabel={`Approve ${shown.length}`} busy={bulkBusy}
          onCancel={() => setBulk(false)} onConfirm={approveAll}>
          <p>Each goes out at its time, one post per channel at a time. Check Going out for the times.</p>
        </ConfirmSheet>
      )}
      <UndoBar pending={pending} onUndo={undo} />
    </div>
  )
}
