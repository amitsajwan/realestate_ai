'use client'
import Link from 'next/link'
import React from 'react'
import { getNotifications, type AppNotification } from '@/lib/app/whatsapp'

/** "New WhatsApp lead", "Website chat needs you", ... for the badge line: what most of the unread alerts are about. */
export function alertsLabel(items: AppNotification[], count: number): string {
  const kinds = new Set(items.map((n) => (n.kind.includes('whatsapp') ? 'whatsapp' : n.kind.includes('chat') ? 'chat' : 'other')))
  const where = kinds.size === 1 && kinds.has('whatsapp') ? 'WhatsApp ' : kinds.size === 1 && kinds.has('chat') ? 'website chat ' : ''
  const noun = count === 1 ? `New ${where}lead or chat` : `New ${where}leads and chats`
  return noun.charAt(0).toUpperCase() + noun.slice(1)
}

/**
 * Studio badge for unread in-app alerts of every kind: new leads and chats that need the agent from WhatsApp and from the website chat
 * (no paid WhatsApp alerts yet). Counts the server's `unread`, so a new kind of alert shows without a change here.
 */
export function LeadAlertsBadge() {
  const [state, setState] = React.useState<{ count: number; items: AppNotification[] }>({ count: 0, items: [] })
  React.useEffect(() => {
    let live = true
    getNotifications(true)
      .then((n) => live && setState({ count: n.unread || n.items.length, items: n.items }))
      .catch(() => undefined)
    return () => {
      live = false
    }
  }, [])
  const { count, items } = state
  if (!count) return null
  return (
    <Link href="/studio/interest" data-testid="lead-alerts-badge"
      className="flex min-h-[56px] items-center justify-between rounded-2xl border border-green-300 bg-green-50 px-4 font-semibold text-green-900">
      <span>
        <span aria-label={`${count} new`} className="mr-2 inline-flex h-6 min-w-[24px] items-center justify-center rounded-full bg-green-700 px-2 text-sm text-white">{count}</span>
        {alertsLabel(items, count)}
      </span>
      <span aria-hidden>&rsaquo;</span>
    </Link>
  )
}

export default LeadAlertsBadge
