'use client'
import Link from 'next/link'
import React from 'react'
import { brandingApi, type BrandingDoc } from '@/lib/app/branding'
import { useIsOwner } from './agents/useIsOwner'

/** True while the agent owes his MahaRERA agent number and the server has set a date for it. */
export function reraDue(doc: BrandingDoc | null | undefined): boolean {
  return !!doc && !doc.branding_data?.rera_agent_no && !!doc.rera_due_at
}

/**
 * Studio home, for an agent who has not given his MahaRERA agent number: what is needed, by when, and a button straight to the box
 * (My brand, #brand-rera). Past the date it says the account may be paused. Not shown to the owner.
 */
export function ReraReminder({ brand }: { brand?: BrandingDoc | null }) {
  const owner = useIsOwner()
  const [loaded, setDoc] = React.useState<BrandingDoc | null>(null)
  React.useEffect(() => {
    if (brand !== undefined) return  // the home screen already has it
    let alive = true
    brandingApi.load().then((d) => alive && setDoc(d)).catch(() => undefined)
    return () => {
      alive = false
    }
  }, [brand])
  const doc = brand !== undefined ? brand : loaded
  if (owner || !reraDue(doc)) return null
  const d = doc as BrandingDoc & { rera_due_at: string }
  const due = new Date(d.rera_due_at)
  const late = due.getTime() < Date.now()
  const day = due.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  return (
    <Link href="/studio/profile#brand-rera" data-testid="rera-reminder"
      className={`block rounded-2xl border p-4 ${late ? 'border-red-300 bg-red-50 text-red-900' : 'border-amber-300 bg-amber-50 text-amber-900'}`}>
      <p className="font-semibold">{late ? 'Add your MahaRERA agent number now' : `Add your MahaRERA agent number by ${day}`}</p>
      <p className="mt-1 text-sm">
        {late ? 'Your account may be paused until you add it.' : 'It is needed to keep your account active. Without it your account may be paused.'}
        {' '}It shows on your website and your posts, like A52100012345.
      </p>
      <span className="mt-3 inline-flex min-h-[44px] items-center rounded-xl bg-white px-4 font-semibold shadow-sm">Add RERA number &rsaquo;</span>
    </Link>
  )
}
