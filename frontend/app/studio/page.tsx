'use client'
import Link from 'next/link'
import React from 'react'
import { BusinessToday } from '@/components/app/BusinessToday'
import { WeeklyCard } from '@/components/app/WeeklyCard'
import { getNotifications } from '@/lib/app/whatsapp'

/** Badge for new WhatsApp leads and chats that need the agent (in-app notifications; no paid WhatsApp alerts yet). */
function WhatsAppBadge() {
  const [count, setCount] = React.useState(0)
  React.useEffect(() => {
    let live = true
    getNotifications(true)
      .then((n) => live && setCount(n.items.filter((x) => x.kind.includes('whatsapp')).length))
      .catch(() => undefined)
    return () => {
      live = false
    }
  }, [])
  if (!count) return null
  return (
    <Link href="/studio/interest" className="flex min-h-[56px] items-center justify-between rounded-2xl border border-green-300 bg-green-50 px-4 font-semibold text-green-900">
      <span>
        <span aria-label={`${count} new`} className="mr-2 inline-flex h-6 min-w-[24px] items-center justify-center rounded-full bg-green-700 px-2 text-sm text-white">{count}</span>
        {count === 1 ? 'New WhatsApp lead or chat' : 'New WhatsApp leads and chats'}
      </span>
      <span aria-hidden>&rsaquo;</span>
    </Link>
  )
}

export default function StudioHome() {
  return (
    <div className="space-y-4">
      <WhatsAppBadge />
      <BusinessToday />
      <WeeklyCard />
      <Link href="/studio/profile" className="flex min-h-[56px] items-center justify-between rounded-2xl border border-gray-200 bg-white px-4 font-semibold text-gray-900">
        <span>My brand: logo, banner and colours</span>
        <span aria-hidden>&rsaquo;</span>
      </Link>
    </div>
  )
}
