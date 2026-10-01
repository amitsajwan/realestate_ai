import type { Metadata } from 'next'
import React from 'react'
import { StudioGate } from '@/components/app/StudioGate'
import { BRAND_NAME } from '@/lib/brand'

export const metadata: Metadata = { title: `My studio - ${BRAND_NAME}` }

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  return <StudioGate>{children}</StudioGate>
}
