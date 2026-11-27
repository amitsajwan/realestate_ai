'use client'
import React, { useState } from 'react'
import { ShareBar } from '@/components/app/ShareBar'
import { Btn } from '@/components/app/ui'
import { markSiteShared } from '@/lib/app/home'
import { copyText } from '@/lib/app/share'
import { t } from '@shared/strings'

/** The site link for a bio, tagged src=bio so a lead from it says so (Leads → source "bio"). Links from accounts Google already
 *  knows (Instagram, WhatsApp Business) also bring the site visits and mentions a young site needs (visibility-base.md step 4). */
export function bioLink(siteUrl: string): string {
  return siteUrl + (siteUrl.includes('?') ? '&' : '?') + 'src=bio'
}

/** The agent's website link with WhatsApp share and copy (My brand). Sharing ticks "Share your website" on the home setup list. */
export function SiteCard({ siteUrl }: { siteUrl: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <h2 className="font-semibold">{t('mySite')}</h2>
      <a href={siteUrl} target="_blank" rel="noopener noreferrer" className="block break-all text-blue-700 underline">
        {siteUrl}
      </a>
      <ShareBar url={siteUrl} message="Namaste! Visit my property website:" onShare={markSiteShared} />
      <p className="text-sm text-gray-600">{t('bioLinkHelp')}</p>
      <Btn variant="secondary" data-testid="copy-bio-link" onClick={async () => {
        const ok = await copyText(bioLink(siteUrl))
        setCopied(ok)
        setTimeout(() => setCopied(false), 2000)
      }}>
        {copied ? t('copied') : t('copyBioLink')}
      </Btn>
    </section>
  )
}
