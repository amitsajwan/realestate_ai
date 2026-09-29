import type { Metadata } from 'next'
import React from 'react'
import { StudioGate } from '@/components/app/StudioGate'

export const metadata: Metadata = { title: 'My studio - PropertyAI' }

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  return <StudioGate>{children}</StudioGate>
}
