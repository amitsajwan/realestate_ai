'use client'
import { usePathname } from 'next/navigation'
import React from 'react'
import { useSession } from '@/lib/app/session'
import { AppShell } from './AppShell'
import { Spinner } from './ui'

/** Session guard + phone shell for everything under /studio. */
export function StudioGate({ children }: { children: React.ReactNode }) {
  const session = useSession(true)
  const path = usePathname() || ''
  const authed = session.ready && !!session.token
  return (
    <AppShell hideTabs={path.startsWith('/studio/listings/new')}>
      {authed ? children : <Spinner />}
    </AppShell>
  )
}
