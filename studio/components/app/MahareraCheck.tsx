'use client'
import Link from 'next/link'
import React from 'react'
import { api } from '@/lib/app/client'
import { useAsync } from '@/lib/app/useAsync'
import type { MahareraMismatch } from '@/lib/app/types'

const FIELD: Record<MahareraMismatch['field'], string> = { project_name: 'Project name', locality: 'Area', possession: 'Possession' }

/** Where the listing disagrees with the MahaRERA record of its own number. It only asks: the agent may know better, so nothing is
 *  changed for them, and a failed check shows nothing rather than an error on the listing's first screen. */
export function MahareraCheck({ id, version, editHref }: { id: string; version?: string | null; editHref: string }) {
  const { data } = useAsync(() => api.mahareraCheck(id), [id, version])
  if (!data?.length) return null
  return (
    <section aria-label="Check against MahaRERA" data-testid="maharera-check" className="space-y-2 rounded-2xl border border-amber-300 bg-amber-50 p-4">
      <h2 className="font-bold text-gray-900">Check these against MahaRERA</h2>
      <p className="text-sm text-gray-700">Buyers see MahaRERA&apos;s record too, so a difference makes them doubt the listing.</p>
      <ul className="space-y-1 text-sm text-gray-900">
        {data.map((m) => <li key={m.field}><b>{FIELD[m.field]}:</b> you wrote {m.yours}, MahaRERA says {m.maharera}</li>)}
      </ul>
      <Link href={editHref} replace scroll={false} className="flex min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline underline-offset-4">Edit the listing</Link>
    </section>
  )
}
