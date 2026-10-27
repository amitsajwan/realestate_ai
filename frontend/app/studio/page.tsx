'use client'
import React from 'react'
import { TodayScreen } from '@/components/app/home/TodayScreen'

/**
 * Studio home (2026-10-27): one call list and one to-do list instead of "Needs you now", "AI recommends" and "Hot buyers", which
 * named the same people three times. Lead counts live on Leads, "This month" on Results, the website link and log out on My brand.
 */
export default function StudioHome() {
  return <TodayScreen />
}
