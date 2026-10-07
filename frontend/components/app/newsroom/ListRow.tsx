'use client'
import React from 'react'
import { LinkOut, StatusPill } from '@/components/app/list'
import type { PillTone } from '@/components/app/list'
import { dueLabel } from '@/lib/app/content'
import type { NewsroomListItem } from '@/lib/app/newsroom'
import { AreaChips } from './QueueCard'

/** The one status a handled item is in, in plain words, with its time. */
export function listStatus(i: NewsroomListItem): { tone: PillTone; text: string; at: string | null } {
  if (i.status === 'published') return { tone: 'ok', text: 'Posted', at: i.published_at ?? i.updated_at }
  if (i.status === 'rejected') return { tone: 'muted', text: 'Rejected', at: i.updated_at }
  if (i.scheduled_for) return { tone: 'info', text: 'Goes out', at: i.scheduled_for }
  return { tone: 'info', text: 'Goes out on the next run', at: null }
}

/** A scheduled, published or rejected item: title, areas, one status with its time, where it went (or why not). Nothing to act on. */
export function ListRow({ item }: { item: NewsroomListItem }) {
  const st = listStatus(item)
  const links: Array<[string, string]> = []
  if (item.permalinks.facebook) links.push(['Facebook', item.permalinks.facebook])
  if (item.permalinks.instagram) links.push(['Instagram', item.permalinks.instagram])
  if (item.news_url) links.push(['News page', item.news_url])
  return (
    <li className="list-none space-y-1 rounded-2xl border border-gray-200 bg-white p-3" data-testid="list-row">
      <p className="text-[15px] font-semibold leading-snug text-gray-900" data-testid="row-title">{item.title}</p>
      <p className="flex-wrap items-center gap-1.5 text-xs text-gray-600 tabular-nums [display:flex]">
        <AreaChips areas={item.areas} />
        <StatusPill tone={st.tone}>{st.text}</StatusPill>
        {st.at && <time dateTime={st.at} data-testid="row-time">{dueLabel(st.at)}</time>}
      </p>
      {item.status === 'rejected' && item.reason && <p className="text-sm text-gray-700" data-testid="row-reason">Reason: {item.reason}</p>}
      {links.length > 0 && (
        <p className="flex-wrap items-center gap-x-2 [display:flex]" data-testid="row-links">
          {links.map(([label, href], n) => (
            <React.Fragment key={label}>
              {n > 0 && <span aria-hidden className="text-gray-400">·</span>}
              <LinkOut href={href} label={label === 'News page' ? 'on our site' : `on ${label}`}>{label}</LinkOut>
            </React.Fragment>
          ))}
        </p>
      )}
    </li>
  )
}
