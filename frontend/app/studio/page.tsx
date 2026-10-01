'use client'
import Link from 'next/link'
import React from 'react'
import { BusinessToday } from '@/components/app/BusinessToday'
import { WeeklyCard } from '@/components/app/WeeklyCard'

export default function StudioHome() {
  return (
    <div className="space-y-4">
      <BusinessToday />
      <WeeklyCard />
      <Link href="/studio/profile" className="flex min-h-[56px] items-center justify-between rounded-2xl border border-gray-200 bg-white px-4 font-semibold text-gray-900">
        <span>My brand: logo, banner and colours</span>
        <span aria-hidden>&rsaquo;</span>
      </Link>
    </div>
  )
}
