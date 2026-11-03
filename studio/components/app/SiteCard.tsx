'use client'
import React from 'react'
import { ShareBar } from '@/components/app/ShareBar'
import { markSiteShared } from '@/lib/app/home'
import { t } from '@shared/strings'

/** The agent's website link with WhatsApp share and copy (My brand). Sharing ticks "Share your website" on the home setup list. */
export function SiteCard({ siteUrl }: { siteUrl: string }) {
  return (
    <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <h2 className="font-semibold">{t('mySite')}</h2>
      <a href={siteUrl} target="_blank" rel="noopener noreferrer" className="block break-all text-blue-700 underline">
        {siteUrl}
      </a>
      <ShareBar url={siteUrl} message="Namaste! Visit my property website:" onShare={markSiteShared} />
    </section>
  )
}
