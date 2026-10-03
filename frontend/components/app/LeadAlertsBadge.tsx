'use client'
import Link from 'next/link'
import React from 'react'
import { getNotifications, type AppNotification } from '@/lib/app/whatsapp'

/** "New WhatsApp lead", "Website chat needs you", ... for the badge line: what most of the unread alerts are about. */
export function alertsLabel(items: AppNotification[], count: number): string {
  const kinds = new Set(items.map((n) => (n.kind.includes('whatsapp') ? 'whatsapp' : n.kind.includes('chat') ? 'chat' : 'other')))
  // "New WhatsApp lead or chat", "New lead or chat from your website" (not "New website chat lead or chat"), "New leads and chats"
  const one = kinds.size === 1
  const noun = count === 1 ? 'lead or chat' : 'leads and chats'
  if (one && kinds.has('whatsapp')) return `New WhatsApp ${noun}`
  if (one && kinds.has('chat')) return `New ${noun} from your website`
  return `New ${noun}`
}

/**
 * Studio badge for unread in-app alerts of every kind: new leads and chats that need the agent from WhatsApp and from the website chat
 * (no paid WhatsApp alerts yet), and for the owner, new website requests to join (a separate badge to Studio > Admin). Counts the
 * server's `unread`, so a new kind of alert shows without a change here.
 */
export const INVITE_KIND = 'invite_request'

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
  // website requests to join (owner only) open the admin queue; everything else is a lead or chat
  const invites = items.filter((n) => n.kind === INVITE_KIND).length
  const leads = Math.max(0, count - invites)
  return (
    <>
      {invites > 0 && (
        <Link href="/studio/admin" data-testid="invite-alerts-badge"
          className="flex min-h-[56px] items-center justify-between rounded-2xl border border-amber-300 bg-amber-50 px-4 font-semibold text-amber-900">
          <span>
            <span aria-label={`${invites} new`} className="mr-2 inline-flex h-6 min-w-[24px] items-center justify-center rounded-full bg-amber-600 px-2 text-sm text-white">{invites}</span>
            {invites === 1 ? 'New request to join' : 'New requests to join'}
          </span>
          <span aria-hidden>&rsaquo;</span>
        </Link>
      )}
      {leads > 0 && (
        <Link href="/studio/interest" data-testid="lead-alerts-badge"
          className="flex min-h-[56px] items-center justify-between rounded-2xl border border-green-300 bg-green-50 px-4 font-semibold text-green-900">
          <span>
            <span aria-label={`${leads} new`} className="mr-2 inline-flex h-6 min-w-[24px] items-center justify-center rounded-full bg-green-700 px-2 text-sm text-white">{leads}</span>
            {alertsLabel(items.filter((n) => n.kind !== INVITE_KIND), leads)}
          </span>
          <span aria-hidden>&rsaquo;</span>
        </Link>
      )}
    </>
  )
}

export default LeadAlertsBadge
