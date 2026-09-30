'use client'
import React from 'react'
import { ErrorBox, PageTitle, Spinner } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { FacebookInterest } from '@/lib/app/types'

const CHIP: Record<string, string> = {
  interested: 'bg-green-100 text-green-800',
  question: 'bg-blue-100 text-blue-800',
  praise: 'bg-pink-100 text-pink-800',
  complaint: 'bg-red-100 text-red-800',
  other: 'bg-gray-100 text-gray-700',
}

function Row({ c }: { c: FacebookInterest }) {
  return (
    <li className={'space-y-2 rounded-2xl border bg-white p-4 ' + (c.needs_human ? 'border-amber-400' : 'border-gray-200')}>
      <div className="flex items-center justify-between gap-2">
        <p className="font-semibold">{c.from_name || 'Someone'}</p>
        <span className={'rounded-full px-2.5 py-0.5 text-xs font-semibold ' + (CHIP[c.intent] ?? CHIP.other)}>{c.intent}</span>
      </div>
      <p className="text-gray-800">&ldquo;{c.text}&rdquo;</p>
      {c.needs_human && <p role="note" className="rounded-lg bg-amber-50 p-2 text-sm font-semibold text-amber-900">Needs you: {c.reason || 'please answer this one'}</p>}
      {c.reply && (
        <p className="rounded-lg bg-gray-50 p-2 text-sm text-gray-700">
          <span className="font-semibold">{c.status === 'replied' ? 'We replied: ' : c.status === 'dry_run' ? 'Would reply (test mode): ' : 'Draft reply: '}</span>{c.reply}
        </p>
      )}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>{c.created_time ? timeAgo(c.created_time) : ''}</span>
        {c.permalink && <a href={c.permalink} target="_blank" rel="noopener noreferrer" className="flex min-h-[44px] items-center font-semibold text-blue-700 underline">Open on Facebook</a>}
      </div>
    </li>
  )
}

export default function InterestPage() {
  const { data, error, loading } = useAsync(() => api.getFacebookInterest(), [])
  if (loading && !data) return <Spinner />
  if (error) return <ErrorBox message={error} />
  const items = data ?? []
  const needs = items.filter((c) => c.needs_human)
  return (
    <div className="space-y-4">
      <PageTitle>{t('interest')}</PageTitle>
      <p className="text-sm text-gray-600">People who commented on your posts on the PUNE Property Page. Interested people are answered automatically; questions we cannot answer wait here for you.</p>
      {items.length === 0 ? (
        <p className="rounded-2xl bg-white p-6 text-center text-gray-600">No comments yet. When someone comments INTERESTED on a post, they show up here.</p>
      ) : (
        <>
          {needs.length > 0 && <p className="rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-900">{needs.length} need{needs.length === 1 ? 's' : ''} you</p>}
          <ul className="space-y-3">{items.map((c) => <Row key={c.id} c={c} />)}</ul>
        </>
      )}
    </div>
  )
}
