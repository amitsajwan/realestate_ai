'use client'
import Link from 'next/link'
import React from 'react'
import { ShareBar } from '@/components/app/ShareBar'
import { ErrorBox, LinkBtn, TempChip } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { useSession } from '@/lib/app/session'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Temperature } from '@/lib/app/types'

export default function StudioHome() {
  const { siteUrl, logout } = useSession(false)
  const stats = useAsync(async () => {
    const [listings, leads] = await Promise.all([api.listListings(), api.listLeads()])
    const temps: Record<Temperature, number> = { hot: 0, warm: 0, cold: 0 }
    leads.forEach((l) => (temps[l.temperature] += 1))
    return { live: listings.filter((l) => l.status === 'live').length, total: listings.length, temps, leads: leads.length }
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('hello')} 🙏</h1>
        <button type="button" onClick={logout} className="min-h-[44px] px-2 text-sm text-gray-500 underline">
          {t('logout')}
        </button>
      </div>

      <LinkBtn href="/studio/listings/new" className="!min-h-[64px] text-lg">
        {t('addListing')}
      </LinkBtn>

      {siteUrl && (
        <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
          <h2 className="font-semibold">{t('mySite')}</h2>
          <a href={siteUrl} target="_blank" rel="noopener noreferrer" className="block break-all text-blue-700 underline">
            {siteUrl}
          </a>
          <ShareBar url={siteUrl} message="Namaste! Visit my property website:" />
        </section>
      )}

      {stats.error && <ErrorBox message={stats.error} onRetry={stats.reload} />}
      {stats.data && (
        <section className="grid grid-cols-2 gap-3">
          <Link href="/studio/listings" className="rounded-2xl border border-gray-200 bg-white p-4">
            <p className="text-3xl font-bold">{stats.data.live}</p>
            <p className="text-sm text-gray-500">Live of {stats.data.total} {t('listings')}</p>
          </Link>
          <Link href="/studio/leads" className="rounded-2xl border border-gray-200 bg-white p-4">
            <p className="text-3xl font-bold">{stats.data.leads}</p>
            <p className="mb-1 text-sm text-gray-500">{t('leads')}</p>
            <div className="flex flex-wrap gap-1">
              {(['hot', 'warm', 'cold'] as Temperature[]).map((k) => (
                <span key={k} className="flex items-center gap-1">
                  <TempChip temperature={k} />
                  <b className="text-xs">{stats.data!.temps[k]}</b>
                </span>
              ))}
            </div>
          </Link>
        </section>
      )}
    </div>
  )
}
