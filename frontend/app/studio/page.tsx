'use client'
import Link from 'next/link'
import React from 'react'
import { useIsOwner } from '@/components/app/agents/useIsOwner'
import { BusinessToday } from '@/components/app/BusinessToday'
import { NeedsYouNow } from '@/components/app/NeedsYouNow'
import { ReraReminder } from '@/components/app/ReraReminder'
import { WeeklyCard } from '@/components/app/WeeklyCard'
import { t } from '@/lib/app/strings'

const rowCls = 'flex min-h-[56px] items-center justify-between rounded-2xl border border-gray-200 bg-white px-4 font-semibold text-gray-900'

/**
 * Studio home, top to bottom: what needs you now, what to do next, this week's numbers. Everything else sits on its own tab
 * (2026-10-18): lead counts and follow-ups on Leads, "This month" on Results, the website link and log out on My brand.
 * Agents have no My brand or Radar tab, so those two stay here as rows; the owner finds them under More.
 */
export default function StudioHome() {
  const owner = useIsOwner()
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{t('todayTitle')}</h1>
      <ReraReminder />
      <NeedsYouNow />
      <BusinessToday />
      <WeeklyCard />
      {!owner && (
        <>
          <Link href="/studio/radar" className={rowCls}>
            <span>Buyer radar: people asking about homes</span>
            <span aria-hidden>&rsaquo;</span>
          </Link>
          <Link href="/studio/profile" className={rowCls}>
            <span>My brand and website</span>
            <span aria-hidden>&rsaquo;</span>
          </Link>
        </>
      )}
    </div>
  )
}
