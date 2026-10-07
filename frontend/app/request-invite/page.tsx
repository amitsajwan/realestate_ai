import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import MarketingShell from '@/components/marketing/MarketingShell'
import RequestInviteForm from '@/components/marketing/RequestInviteForm'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { INVITE, PATHS } from '@/lib/marketing/strings'

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: INVITE.metaTitle,
  description: INVITE.metaDescription,
  path: PATHS.invite,
})

export default function RequestInvitePage() {
  return (
    <MarketingShell cta="none">
      <section aria-labelledby="invite-title" className="mx-auto max-w-xl px-4 py-10 sm:py-14">
        <h1 id="invite-title" className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{INVITE.title}</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-700">{INVITE.lead}</p>
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <RequestInviteForm />
        </div>
        <p className="mt-6 text-sm text-slate-700">
          {INVITE.signInHint}{' '}
          <Link href={PATHS.signIn} className="font-medium text-[#0f2340] underline">Sign in</Link>
        </p>
      </section>
    </MarketingShell>
  )
}
