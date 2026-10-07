'use client'
import React from 'react'
import { Chip } from '@/components/app/ui'
import { LinkOut } from '@/components/app/list'
import { channelLabel, dueLabel, groupItems } from '@/lib/app/content'
import type { ContentItem } from '@/lib/app/content'

/** Posts that are out (each channel with its link) or that failed (with the reason), newest first. */
export function PostedList({ items, kind }: { items: ContentItem[]; kind: 'posted' | 'problems' }) {
  const groups = groupItems(items)
  if (groups.length === 0) {
    return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">{kind === 'posted' ? 'Nothing posted in the last 3 days.' : 'No problems.'}</p>
  }
  return (
    <ul className="space-y-2 p-0" data-testid={kind}>
      {groups.map((g) => {
        const first = g.items[0]
        const title = (first.caption.split('\n').find((l) => l.trim()) || first.slug).slice(0, 90)
        return (
          <li key={g.key} className="list-none rounded-2xl border border-gray-200 bg-white p-3">
            <p className="text-sm font-semibold text-gray-900">{title}</p>
            <ul className="mt-1 space-y-1 p-0">
              {g.items.map((i) => (
                <li key={i.id} className="flex list-none flex-wrap items-center gap-2 text-sm">
                  <Chip tone={i.channel === 'instagram' ? 'purple' : 'blue'}>{channelLabel(i.channel)}</Chip>
                  {i.status === 'published' ? (
                    <>
                      <span className="text-gray-600">posted {i.published_at ? dueLabel(i.published_at) : ''}</span>
                      {i.permalink && <LinkOut href={i.permalink} label={`on ${channelLabel(i.channel)}`}>Open post</LinkOut>}
                    </>
                  ) : i.status === 'removed' ? (
                    <span className="text-gray-600">deleted on {channelLabel(i.channel)}</span>
                  ) : (
                    <span className="text-red-700">not posted: {i.error || i.note || 'failed'}</span>
                  )}
                </li>
              ))}
            </ul>
          </li>
        )
      })}
    </ul>
  )
}
