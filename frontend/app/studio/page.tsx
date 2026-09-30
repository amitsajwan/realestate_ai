'use client'
import React from 'react'
import { BusinessToday } from '@/components/app/BusinessToday'
import { WeeklyCard } from '@/components/app/WeeklyCard'

export default function StudioHome() {
  return (
    <div className="space-y-4">
      <BusinessToday />
      <WeeklyCard />
    </div>
  )
}
